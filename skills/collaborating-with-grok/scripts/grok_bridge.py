#!/usr/bin/env python3
"""
Grok CLI Bridge Script.

Wraps the Grok CLI (`grok -p`, headless mode) to provide a JSON interface,
live stderr progress, and multi-turn continuity via SESSION_ID.

Verified against `grok` (Grok Build TUI) v0.2.93 on macOS. Facts the bridge
relies on:

  * Headless `grok -p` streams cleanly to a pipe (no TTY required) and exits on
    its own — no pseudo-terminal needed (unlike the Antigravity CLI).
  * `--output-format streaming-json` emits newline-delimited JSON events:
        {"type":"thought","data":"..."}   reasoning tokens
        {"type":"text","data":"..."}      answer tokens
        {"type":"end","stopReason":"EndTurn","sessionId":"...","requestId":"..."}
    Tool calls are NOT surfaced as events in headless mode (rich tool/plan
    updates are an ACP-mode feature of `grok agent stdio`). The bridge recovers
    tool telemetry after the run from the session files under
    `~/.grok/sessions/<encoded-cwd>/<session-id>/` (updates.jsonl for tool
    calls, summary.json for the model that actually answered — the host's
    ~/.grok/config.toml `[models] default` may override the CLI default).
    Session paths are encoded from the resolved cwd (symlinks matter: macOS
    `/tmp` → `/private/tmp`).
  * `--output-format json` emits a single object:
        {"text":..,"stopReason":..,"sessionId":..,"requestId":..,"thought":..}
  * `sessionId` appears only in the terminal `end`/json object. Resume a prior
    session with `-r <sessionId>` (errors if the session does not exist).
  * The exit code is the authoritative success signal; `stopReason` is the
    completeness signal. An approval-gated action is *cancelled* in headless
    mode (stopReason "Cancelled", exit 0, files untouched) — it never hangs.
    A `--max-turns` cutoff is stopReason "Cancelled" with a NON-zero exit and an
    `Error:` line on stderr.

Safety: the user's `~/.grok/config.toml` may set
`permission_mode = "always-approve"`, which auto-approves edits and shell
commands. To keep write/shell authority approval-gated by default, the bridge passes
`--permission-mode default` unless the caller chooses a mutually exclusive
authority flag. A standalone `--always-approve` grants explicit write/shell
authority; it is never combined with the safe default.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

OUTPUT_FORMATS = ("plain", "json", "streaming-json")
PERMISSION_MODES = ("default", "plan", "acceptEdits", "auto", "dontAsk", "bypassPermissions")
ENFORCED_CLI_PERMISSION_MODES = ("default", "bypassPermissions")
UNWIRED_CLI_PERMISSION_MODES = tuple(
    mode for mode in PERMISSION_MODES if mode not in ENFORCED_CLI_PERMISSION_MODES
)
BUILTIN_SANDBOX_PROFILES = ("off", "workspace", "devbox", "read-only", "strict")
EFFORT_LEVELS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")

# Grok prints ANSI-coloured log lines to stderr (e.g. "\x1b[2m...\x1b[0m").
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[=>]")
# stderr lines worth surfacing as the failure reason.
ERROR_LINE_RE = re.compile(r"(^|\s)(Error:|ERROR\b|panicked|fatal)", re.IGNORECASE)


def emit_json(result: Dict[str, Any], exit_code: int = 0) -> None:
    result.setdefault("complete", False)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)


def find_executable(name: str) -> str:
    """Locate the grok executable, handling a Windows `.exe`/`.cmd` shim."""
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        for ext in (".exe", ".cmd", ".bat"):
            alt = shutil.which(f"{name}{ext}")
            if alt:
                return alt
    return name


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_sandbox_profile(value: str) -> str:
    """Preserve built-in/custom profile names with a targeted Codex-term hint."""
    if value == "":
        return value
    if value == "workspace-write":
        raise argparse.ArgumentTypeError(
            "Grok calls this profile 'workspace'; use `--sandbox workspace` "
            "(`workspace-write` is Codex CLI terminology)."
        )
    # Grok also accepts names from global/project sandbox.toml files and
    # validates unknown profiles fail-closed.
    return value


def resolve_workspace_path(path: Path, cd: Path) -> Path:
    """Resolve an input path, using --cd as the base for relative paths."""
    expanded = path.expanduser()
    if not expanded.is_absolute():
        expanded = cd / expanded
    return expanded.resolve()


def permission_mode_error(mode: Optional[str]) -> Optional[str]:
    """Reject modes that Grok 0.2.93 parses but does not enforce from the CLI."""
    if mode not in UNWIRED_CLI_PERMISSION_MODES:
        return None
    return (
        f"`--permission-mode {mode}` is accepted but not enforced by Grok CLI 0.2.93. "
        "The bridge refuses to provide a false authority or safety signal. Use `default`, "
        "explicit `--allow`/`--deny` rules, or `--always-approve`/`bypassPermissions` only "
        "with user consent. For acceptEdits/dontAsk policy, configure `defaultMode` in the "
        "applicable `.claude/settings.json`."
    )


def materialize_context_prompt(
    prompt: str,
    context_file: Path,
    temp_dir: Optional[Path] = None,
) -> Path:
    """Combine an instruction and context file into a native prompt file.

    Grok 0.2.93 ignores stdin when `-p` is present. A temporary prompt file
    preserves large-file behavior without putting the context on argv.
    """
    context = context_file.read_text(encoding="utf-8", errors="replace")
    fd, name = tempfile.mkstemp(
        prefix="grok-bridge-context-",
        suffix=".md",
        dir=str(temp_dir) if temp_dir is not None else None,
        text=True,
    )
    path = Path(name)
    payload = json.dumps(
        {"source": context_file.as_posix(), "content": context},
        ensure_ascii=False,
    )
    # Prevent context text from closing the XML wrapper. JSON escapes remain
    # legible to the model while keeping arbitrary file contents data-only.
    payload = (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(prompt.rstrip())
            handle.write('\n\n<context_file format="json" trust="untrusted-data">\n')
            handle.write(payload)
            handle.write("\n</context_file>\n")
    except BaseException:
        # os.fdopen owns fd after it succeeds; close defensively when it fails.
        try:
            os.close(fd)
        except OSError:
            pass
        path.unlink(missing_ok=True)
        raise
    return path


def find_ancestor_git_root(cd: Path) -> Optional[Path]:
    """Return the nearest Git root marker at or above cd, if one exists."""
    for candidate in (cd, *cd.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def completion_state(
    success: bool,
    output_format: str,
    stop_reason: Optional[str],
) -> Optional[bool]:
    """Return known completion, or None when plain output hides stopReason."""
    if not success:
        return False
    if output_format == "plain":
        return None
    return stop_reason == "EndTurn"


def session_recovery_warning(output_format: str) -> str:
    if output_format == "plain":
        return (
            "SESSION_ID recovered from session storage; plain output does not emit it, so resume "
            "is available on a best-effort basis."
        )
    return (
        "SESSION_ID was recovered from the session directory because grok ended before emitting "
        "it; resume with `--SESSION_ID` to continue."
    )


def configuration_warnings(args: argparse.Namespace, cd: Path) -> List[str]:
    """Describe authority, observability, and isolation sharp edges."""
    warnings: List[str] = []
    if args.always_approve:
        warnings.append(
            "`--always-approve` auto-approves all grok tool actions "
            "(writes + shell) without prompting."
        )
    if args.permission_mode == "bypassPermissions":
        warnings.append(
            f"`--permission-mode {args.permission_mode}` reduces approval gating; "
            "grok may edit files or run commands."
        )
    if args.permission_mode == "":
        warnings.append(
            "No `--permission-mode` set: grok inherits ~/.grok/config.toml, which may "
            "auto-approve tools. Omit the flag for the bridge's gated `default` mode."
        )
    if args.output_format == "plain":
        warnings.append(
            "`--output-format plain` cannot capture stopReason, so `complete` will be null."
        )
    if args.sandbox == "workspace":
        warnings.append(
            "`--sandbox workspace` reads everywhere and writes only CWD, ~/.grok, and temp "
            "directories. Prompt scope is not a hard read boundary; use `strict`, a custom "
            "deny profile, or external isolation when required."
        )
    elif args.sandbox == "devbox":
        warnings.append(
            "`--sandbox devbox` permits broad filesystem writes and is intended only for "
            "disposable development VMs."
        )
    elif args.sandbox and args.sandbox not in BUILTIN_SANDBOX_PROFILES:
        warnings.append(
            f"`--sandbox {args.sandbox}` is a custom profile; verify the applicable "
            "sandbox.toml because its read, write, deny, and network rules are external "
            "to this bridge."
        )

    git_root = find_ancestor_git_root(cd)
    if git_root is not None and git_root != cd:
        warnings.append(
            f"`--cd` is nested below Git root {git_root.as_posix()!r}; grok may discover "
            "parent instructions, configuration, and repository metadata. Use a standalone "
            "workspace outside the parent repository for stronger isolation."
        )

    allow_tools = [tool.strip() for tool in args.tools.split(",") if tool.strip()]
    if any(tool in ("run_terminal_cmd", "web_search", "web_fetch") for tool in allow_tools):
        warnings.append(
            "`--tools` allowlist includes run_terminal_cmd or web_search/web_fetch: on the "
            "GrokBuild-lineage coding agent (e.g. grok-4.5) these allowlists fail session build with "
            "run_terminal_cmd's auto-background RequirementError, which is still "
            "present for those tool combinations on CLI 0.2.93. Use a read-only allowlist "
            "without those tools, or keep the default toolset and use `--disallowed-tools`."
        )
    return warnings


def preflight_check(cd: Path) -> Optional[str]:
    if shutil.which("grok") is None:
        return (
            "Grok CLI not found in PATH. Install it "
            "(`curl -fsSL https://x.ai/cli/install.sh | bash`) and ensure `grok` is available."
        )
    if not cd.exists():
        return f"Workspace root `{cd.absolute().as_posix()}` does not exist."
    if not cd.is_dir():
        return f"Workspace root `{cd.absolute().as_posix()}` is not a directory."
    has_env_key = bool(os.environ.get("XAI_API_KEY"))
    has_auth_file = Path.home().joinpath(".grok", "auth.json").is_file()
    if not has_env_key and not has_auth_file:
        return "No Grok auth found. Run `grok login`, or export `XAI_API_KEY`."
    return None


def list_models() -> Dict[str, Any]:
    """Parse `grok models` (plain text) into a JSON-friendly structure."""
    try:
        proc = subprocess.run(
            [find_executable("grok"), "models"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"success": False, "error": f"Failed to run `grok models`: {exc}"}

    text = strip_ansi(proc.stdout)
    models: List[str] = []
    default: Optional[str] = None
    for line in text.splitlines():
        match = re.match(r"\s*([*-])\s+(\S+)", line)
        if not match:
            continue
        bullet, model = match.group(1), match.group(2)
        models.append(model)
        if bullet == "*" or "(default)" in line:
            default = model
    if not models:
        err = strip_ansi(proc.stderr).strip() or "`grok models` returned no models."
        return {"success": False, "error": err}
    return {"success": True, "models": models, "default": default}


def build_command(args: argparse.Namespace, cd: Path, prompt: str) -> List[str]:
    mode_error = permission_mode_error(args.permission_mode)
    if mode_error:
        raise ValueError(mode_error)
    cmd = ["grok"]
    if args.prompt_file is not None:
        cmd.extend(["--prompt-file", str(args.prompt_file)])
    else:
        cmd.extend(["-p", prompt])

    cmd.extend(["--output-format", args.output_format, "--cwd", cd.absolute().as_posix()])

    if args.model:
        cmd.extend(["-m", args.model])

    # Session continuity (mutually exclusive in argparse).
    if args.SESSION_ID:
        cmd.extend(["-r", args.SESSION_ID])
    elif args.session_id:
        cmd.extend(["-s", args.session_id])
    elif args.continue_session:
        cmd.append("-c")

    if args.always_approve and args.permission_mode is not None:
        raise ValueError("--always-approve and --permission-mode are mutually exclusive")
    if args.always_approve:
        cmd.append("--always-approve")
    elif args.permission_mode is None:
        cmd.extend(["--permission-mode", "default"])
    elif args.permission_mode:
        cmd.extend(["--permission-mode", args.permission_mode])
    if args.sandbox:
        cmd.extend(["--sandbox", args.sandbox])
    if args.tools:
        cmd.extend(["--tools", args.tools])
    if args.disallowed_tools:
        cmd.extend(["--disallowed-tools", args.disallowed_tools])
    for rule in args.allow:
        cmd.extend(["--allow", rule])
    for rule in args.deny:
        cmd.extend(["--deny", rule])

    if args.effort:
        cmd.extend(["--effort", args.effort])
    if args.reasoning_effort:
        cmd.extend(["--reasoning-effort", args.reasoning_effort])
    if args.max_turns:
        cmd.extend(["--max-turns", str(args.max_turns)])
    if args.rules:
        cmd.extend(["--rules", args.rules])
    if args.disable_web_search:
        cmd.append("--disable-web-search")
    if args.no_plan:
        cmd.append("--no-plan")
    return cmd


def stream_command(
    cmd: List[str],
    cwd: Path,
    timeout_seconds: float,
    stderr_sink: List[str],
) -> Generator[str, None, int]:
    """Run grok, yield stdout lines, and forward cleaned stderr as progress."""
    resolved = cmd.copy()
    resolved[0] = find_executable(cmd[0])

    proc = subprocess.Popen(
        resolved,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(cwd),
    )

    out_q: "queue.Queue[Optional[str]]" = queue.Queue()
    started_at = time.time()

    def read_stdout() -> None:
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            stripped = line.strip()
            if stripped:
                out_q.put(stripped)
        proc.stdout.close()
        out_q.put(None)

    def read_stderr() -> None:
        assert proc.stderr is not None
        for line in iter(proc.stderr.readline, ""):
            text = strip_ansi(line).rstrip()
            if not text:
                continue
            print(f"[grok stderr] {text}", file=sys.stderr, flush=True)
            if ERROR_LINE_RE.search(text):
                stderr_sink.append(text)
        proc.stderr.close()

    t_out = threading.Thread(target=read_stdout, daemon=True)
    t_err = threading.Thread(target=read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    while True:
        if timeout_seconds and time.time() - started_at > timeout_seconds:
            print(
                f"[grok] timeout after {timeout_seconds:g}s; terminating grok",
                file=sys.stderr,
                flush=True,
            )
            proc.kill()
            proc.wait()
            return 124
        try:
            line = out_q.get(timeout=0.5)
            if line is None:
                break
            yield line
        except queue.Empty:
            if proc.poll() is not None and not t_out.is_alive():
                break

    t_out.join(timeout=5)
    t_err.join(timeout=2)
    try:
        return proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait()


def handle_event(event: Dict[str, Any], state: Dict[str, Any], start_time: float) -> None:
    """Fold one streaming-json event into state and emit throttled progress."""

    def status(message: str) -> None:
        elapsed = time.time() - start_time
        print(f"[grok {elapsed:5.1f}s] {message}", file=sys.stderr, flush=True)

    etype = event.get("type", "")
    if etype == "text":
        data = event.get("data", "")
        state["agent_messages"] += data
        if not state["responding"]:
            state["responding"] = True
            status("Responding…")
            state["last_status"] = time.time()
        elif time.time() - state["last_status"] >= 1.5:
            status(f"Responding… ({len(state['agent_messages'])} chars)")
            state["last_status"] = time.time()
    elif etype == "thought":
        state["reasoning"] += event.get("data", "")
        if not state["thinking"]:
            state["thinking"] = True
            status("Thinking…")
            state["last_status"] = time.time()
        elif time.time() - state["last_status"] >= 1.5:
            status(f"Thinking… ({len(state['reasoning'])} chars)")
            state["last_status"] = time.time()
    elif etype == "end":
        state["stop_reason"] = event.get("stopReason")
        state["session_id"] = event.get("sessionId") or state["session_id"]
        state["request_id"] = event.get("requestId") or state["request_id"]
        preview = state["agent_messages"][:80].replace("\n", " ")
        status(f"Done · {state['stop_reason']} · {preview}{'…' if len(state['agent_messages']) > 80 else ''}")
    elif "error" in etype.lower():
        message = ""
        err = event.get("error")
        if isinstance(err, dict):
            message = str(err.get("message", ""))
        message = message or str(event.get("data") or event.get("message") or "")
        if message:
            state["errors"].append(message)
            status(f"Error event: {message[:80]}")


def parse_json_blob(raw: str, state: Dict[str, Any]) -> None:
    """Parse a single `--output-format json` object."""
    raw = raw.strip()
    if not raw:
        state["errors"].append("No output received from grok.")
        return
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        state["errors"].append(f"Failed to parse grok JSON output: {exc}")
        return
    if not isinstance(obj, dict):
        state["errors"].append("Unexpected grok JSON output (not an object).")
        return
    state["all_messages"].append(obj)
    if isinstance(obj.get("text"), str):
        state["agent_messages"] += obj["text"]
    if isinstance(obj.get("thought"), str):
        state["reasoning"] += obj["thought"]
    state["stop_reason"] = obj.get("stopReason") or state["stop_reason"]
    state["session_id"] = obj.get("sessionId") or state["session_id"]
    state["request_id"] = obj.get("requestId") or state["request_id"]


def session_cwd_encodings(cd: Path) -> List[str]:
    """Return URL-encoded cwd keys grok may use under ~/.grok/sessions/.

    Grok encodes the resolved workspace path. On macOS, `/tmp` is a symlink to
    `/private/tmp`, so absolute() and resolve() can disagree — try both.
    """
    encodings: List[str] = []
    for candidate in (cd.resolve(), cd.absolute()):
        key = urllib.parse.quote(str(candidate), safe="")
        if key not in encodings:
            encodings.append(key)
    return encodings


def snapshot_session_dirs(cd: Path) -> set[str]:
    """Record existing session directories so recovery ignores older runs."""
    existing: set[str] = set()
    try:
        for enc in session_cwd_encodings(cd):
            sessions_root = Path.home() / ".grok" / "sessions" / enc
            if sessions_root.is_dir():
                existing.update(
                    str(path) for path in sessions_root.iterdir() if path.is_dir()
                )
    except OSError:
        pass
    return existing


def collect_session_telemetry(
    cd: Path,
    session_id: Optional[str],
    run_start: float,
    preexisting_session_dirs: Optional[set[str]] = None,
) -> Dict[str, Any]:
    """Recover post-run telemetry from grok's session files.

    Headless grok emits no tool events, but `updates.jsonl` records every tool
    call and `summary.json` records the model that actually answered. Explicit
    resume/new-session IDs provide a deterministic hint. Otherwise,
    recovery considers only session directories absent from the pre-run
    snapshot, then uses mtime. Concurrent new runs in the same cwd remain
    best-effort. Returns {} on any failure.
    """
    telemetry: Dict[str, Any] = {}
    try:
        session_dir: Optional[Path] = None
        for enc in session_cwd_encodings(cd):
            sessions_root = Path.home() / ".grok" / "sessions" / enc
            if session_id and (sessions_root / session_id).is_dir():
                session_dir = sessions_root / session_id
                break
            if sessions_root.is_dir():
                excluded = preexisting_session_dirs or set()
                fresh = [
                    d for d in sessions_root.iterdir()
                    if d.is_dir()
                    and str(d) not in excluded
                    and d.stat().st_mtime >= run_start - 2
                ]
                if fresh:
                    session_dir = max(fresh, key=lambda d: d.stat().st_mtime)
                    telemetry["recovered_session_id"] = session_dir.name
                    break
        if session_dir is None:
            return telemetry
        telemetry["session_id"] = session_dir.name

        summary_path = session_dir / "summary.json"
        if summary_path.is_file():
            summary = json.loads(summary_path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(summary, dict):
                if summary.get("current_model_id"):
                    telemetry["model"] = summary["current_model_id"]
                if summary.get("agent_name"):
                    telemetry["agent"] = summary["agent_name"]

        updates_path = session_dir / "updates.jsonl"
        if updates_path.is_file():
            tool_counts: Dict[str, int] = {}
            last_ts: Optional[str] = None
            with updates_path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    if isinstance(event.get("timestamp"), str):
                        last_ts = event["timestamp"]
                    params = event.get("params")
                    update = params.get("update") if isinstance(params, dict) else None
                    if isinstance(update, dict) and update.get("sessionUpdate") == "tool_call":
                        title = str(update.get("title") or "unknown")
                        tool_counts[title] = tool_counts.get(title, 0) + 1
            if tool_counts:
                telemetry["tool_counts"] = tool_counts
                telemetry["tools_used"] = sorted(tool_counts)
            if last_ts:
                try:
                    parsed = datetime.datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    telemetry["last_activity_age_s"] = round((now - parsed).total_seconds(), 1)
                except ValueError:
                    pass
    except Exception:  # pragma: no cover - telemetry must never break the result
        pass
    return telemetry


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grok CLI Bridge")
    parser.add_argument("--PROMPT", default="", help="Instruction to send to grok. Use this or --prompt-file.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="Read the whole prompt from a file (grok --prompt-file). Relative paths resolve against --cd.")
    parser.add_argument("--stdin-file", type=Path, default=None, help="Combine a context/handoff file with the instruction in --PROMPT. Relative paths resolve against --cd; mutually exclusive with --prompt-file.")
    parser.add_argument("--cd", type=Path, default=None, help="Workspace root for grok (maps to grok --cwd). Required unless --list-models.")
    parser.add_argument("--list-models", action="store_true", help="Print models from `grok models` as JSON and exit (no prompt/--cd needed).")

    session = parser.add_mutually_exclusive_group()
    session.add_argument("--SESSION_ID", default="", help="Resume a session by ID (grok -r; errors if it does not exist).")
    session.add_argument("--session-id", dest="session_id", default="", help="Name a NEW session (grok -s; valid unused UUID; does not resume — use --SESSION_ID/--continue).")
    session.add_argument("--continue", dest="continue_session", action="store_true", help="Continue the most recent session in --cd (grok -c).")

    parser.add_argument("--model", default="", help="Model ID (e.g. grok-4.5 as of CLI 0.2.93). Discover with --list-models — do not hardcode.")
    parser.add_argument("--output-format", default="streaming-json", choices=OUTPUT_FORMATS, help="grok output format. Default streaming-json (live progress + SESSION_ID).")

    authority = parser.add_mutually_exclusive_group()
    authority.add_argument("--permission-mode", default=None, choices=("",) + PERMISSION_MODES, help="Tool-approval mode. Omit for gated 'default'; pass '' to inherit grok config. Grok 0.2.93 only enforces default and bypassPermissions from this CLI flag.")
    authority.add_argument("--always-approve", action="store_true", help="Auto-approve every tool action (writes + shell). Use only with explicit user consent, ideally in an isolated worktree.")
    parser.add_argument("--sandbox", default=None, type=parse_sandbox_profile, help="Grok sandbox profile: off, workspace, devbox, read-only, strict, or a custom sandbox.toml profile.")
    parser.add_argument("--tools", default="", help='Allowlist of built-in tools (comma-separated), e.g. "read_file,grep,list_dir" for hard read-only.')
    parser.add_argument("--disallowed-tools", default="", help='Denylist of built-in tools (comma-separated). Supports Agent / Agent(type) entries.')
    parser.add_argument("--allow", action="append", default=[], help='Permission allow rule, e.g. "Bash(npm*)" or "WebFetch(domain:docs.rs)". Repeatable.')
    parser.add_argument("--deny", action="append", default=[], help='Permission deny rule, e.g. "Bash(rm*)". Repeatable. Deny beats allow.')

    parser.add_argument("--effort", default="", choices=("",) + EFFORT_LEVELS, help="Effort level (model-dependent; CLI alias of --reasoning-effort).")
    parser.add_argument("--reasoning-effort", default="", help="Reasoning effort for models that support it (e.g. grok-4.5).")
    parser.add_argument("--max-turns", type=int, default=0, help="Maximum agentic turns before grok stops (0 = unset).")
    parser.add_argument("--rules", default="", help="Extra rules appended to the system prompt.")
    parser.add_argument("--disable-web-search", action="store_true", help="Remove the web_search/web_fetch tools.")
    parser.add_argument("--no-plan", action="store_true", help="Disable grok plan mode.")

    parser.add_argument("--timeout", type=float, default=0, help="Bridge wall-clock kill, in seconds. Default: no bridge timeout.")
    parser.add_argument("--return-all-messages", action="store_true", help="Include the captured reasoning and raw events in the result.")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    if args.list_models:
        if shutil.which("grok") is None:
            emit_json({"success": False, "error": "Grok CLI not found in PATH."}, exit_code=1)
        result = list_models()
        result["complete"] = bool(result.get("success"))
        emit_json(result, exit_code=0 if result.get("success") else 1)

    mode_error = permission_mode_error(args.permission_mode)
    if mode_error:
        emit_json({"success": False, "error": mode_error}, exit_code=2)

    if args.cd is None:
        emit_json({"success": False, "error": "`--cd` is required (omit it only with --list-models)."}, exit_code=2)
    if args.PROMPT and args.prompt_file is not None:
        emit_json({"success": False, "error": "Use either `--PROMPT` or `--prompt-file`, not both."}, exit_code=2)
    if not args.PROMPT and args.prompt_file is None:
        emit_json({"success": False, "error": "Provide `--PROMPT` or `--prompt-file`."}, exit_code=2)
    if args.prompt_file is not None and args.stdin_file is not None:
        emit_json({"success": False, "error": "Use either `--prompt-file` or `--stdin-file`, not both."}, exit_code=2)
    if args.stdin_file is not None and not args.PROMPT:
        emit_json({"success": False, "error": "`--stdin-file` requires `--PROMPT` (the instruction); the bridge combines both into a native prompt file."}, exit_code=2)
    if args.timeout < 0:
        emit_json({"success": False, "error": "`--timeout` must be zero or a positive number of seconds."}, exit_code=2)

    cd = args.cd.expanduser().resolve()
    if args.prompt_file is not None:
        args.prompt_file = resolve_workspace_path(args.prompt_file, cd)
    if args.stdin_file is not None:
        args.stdin_file = resolve_workspace_path(args.stdin_file, cd)

    prompt = args.PROMPT
    if args.prompt_file is not None:
        if not args.prompt_file.is_file():
            emit_json({"success": False, "error": f"Prompt file not found: {args.prompt_file}"}, exit_code=2)
        if not args.prompt_file.read_text(encoding="utf-8", errors="replace").strip():
            emit_json({"success": False, "error": "Prompt file is empty."}, exit_code=2)
    elif not prompt.strip():
        emit_json({"success": False, "error": "Prompt is empty."}, exit_code=2)
    if args.stdin_file is not None and not args.stdin_file.is_file():
        emit_json({"success": False, "error": f"Stdin context file not found: {args.stdin_file}"}, exit_code=2)

    error = preflight_check(cd)
    if error:
        emit_json({"success": False, "error": error}, exit_code=1)

    warnings = configuration_warnings(args, cd)
    preexisting_session_dirs = snapshot_session_dirs(cd)

    state: Dict[str, Any] = {
        "agent_messages": "",
        "reasoning": "",
        "stop_reason": None,
        "session_id": None,
        "request_id": None,
        "thinking": False,
        "responding": False,
        "last_status": 0.0,
        "errors": [],
        "all_messages": [],
    }
    stderr_sink: List[str] = []
    raw_json_lines: List[str] = []
    start_time = time.time()
    returncode = 1
    temporary_prompt_file: Optional[Path] = None

    try:
        if args.stdin_file is not None:
            temporary_prompt_file = materialize_context_prompt(prompt, args.stdin_file)
            args.prompt_file = temporary_prompt_file
        cmd = build_command(args, cd, prompt)
        generator = stream_command(cmd, cd.absolute(), args.timeout, stderr_sink)
        while True:
            try:
                line = next(generator)
            except StopIteration as finished:
                returncode = int(finished.value or 0)
                break
            if args.output_format == "streaming-json":
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    state["errors"].append(f"[json decode error] {line}")
                    continue
                if isinstance(event, dict):
                    state["all_messages"].append(event)
                    handle_event(event, state, start_time)
            elif args.output_format == "json":
                raw_json_lines.append(line)
            else:  # plain
                state["agent_messages"] += line + "\n"
    except Exception as exc:  # pragma: no cover - defensive boundary
        emit_json({"success": False, "error": f"Failed to run grok: {exc}", "warnings": warnings}, exit_code=1)
    finally:
        if temporary_prompt_file is not None:
            temporary_prompt_file.unlink(missing_ok=True)

    if args.output_format == "json":
        parse_json_blob("\n".join(raw_json_lines), state)
    elif args.output_format == "plain":
        state["agent_messages"] = state["agent_messages"].strip()

    agent_messages = state["agent_messages"]
    stop_reason = state["stop_reason"]

    # Exit code is authoritative; stopReason signals completeness.
    success = returncode == 0
    complete = completion_state(success, args.output_format, stop_reason)
    if success and stop_reason and stop_reason != "EndTurn":
        warnings.append(
            f"grok stopReason={stop_reason!r}: the turn ended without a clean completion "
            "(an approval-gated action may have been cancelled, or output was truncated). "
            "Treat the result as possibly incomplete."
        )
    if success and state["session_id"] is None and args.output_format in ("json", "streaming-json"):
        warnings.append("Could not capture SESSION_ID; multi-turn resume will not be possible for this run.")
    if success and not agent_messages and stop_reason == "EndTurn":
        warnings.append("grok returned an empty response.")

    errors = list(state["errors"])
    if not success:
        errors.extend(stderr_sink)
        if returncode == 124:
            errors.append(f"grok exceeded the bridge timeout of {args.timeout:g}s and was killed.")
        elif returncode != 0:
            errors.append(f"grok exited with non-zero status: {returncode}.")
        if not errors:
            errors.append("No response captured from grok.")

    session_hint = state["session_id"] or args.SESSION_ID or args.session_id or None
    telemetry = collect_session_telemetry(
        cd, session_hint, start_time, preexisting_session_dirs
    )
    telemetry_session_id = telemetry.get("session_id") or telemetry.get("recovered_session_id")
    if state["session_id"] is None and telemetry_session_id:
        state["session_id"] = telemetry_session_id
        warnings.append(session_recovery_warning(args.output_format))
    actual_model = telemetry.get("model") or args.model
    actual_agent = telemetry.get("agent") or ""
    # Only warn when the effective agent is the alternate (composer/cursor) lineage —
    # not on every omit-`--model` coding run. Result still reports `model`/`agent`.
    if not args.model and actual_model:
        composer_like = (
            "composer" in actual_model.lower()
            or actual_agent == "cursor"
            or str(actual_agent).startswith("cursor")
        )
        if composer_like:
            warnings.append(
                f"No `--model` was passed; composer/cursor agent ran: model={actual_model!r}, "
                f"agent={actual_agent or 'unknown'!r}. Tool names and research timing differ from "
                "the GrokBuild-lineage coding model. For search/X or predictable tool ids, pass "
                "`--model` with a coding model from `--list-models` (e.g. grok-4.5 as of 0.2.93)."
            )
    if returncode == 124 and telemetry.get("tool_counts"):
        total_calls = sum(telemetry["tool_counts"].values())
        age = telemetry.get("last_activity_age_s")
        recency = f"; last activity {age:g}s before this report" if isinstance(age, (int, float)) else ""
        warnings.append(
            f"grok was still actively working when killed ({total_calls} tool calls recorded{recency}) — "
            "a slow research loop, not a hang. Rerun with a larger `--timeout` or resume with `--SESSION_ID`."
        )

    result: Dict[str, Any] = {"success": success, "complete": complete}
    if state["session_id"] is not None:
        result["SESSION_ID"] = state["session_id"]
    result["agent_messages"] = agent_messages
    if actual_model:
        result["model"] = actual_model
    if telemetry.get("agent"):
        result["agent"] = telemetry["agent"]
    if telemetry.get("tool_counts"):
        result["tool_counts"] = telemetry["tool_counts"]
        result["tools_used"] = telemetry["tools_used"]
    if stop_reason is not None:
        result["stop_reason"] = stop_reason
    if state["request_id"] is not None:
        result["request_id"] = state["request_id"]
    if warnings:
        result["warnings"] = warnings
    if not success:
        # De-duplicate while preserving order.
        seen: set = set()
        ordered = [e for e in errors if e and not (e in seen or seen.add(e))]
        result["error"] = "\n".join(ordered) or "grok did not return a usable response."
    if args.return_all_messages:
        result["reasoning"] = state["reasoning"]
        result["all_messages"] = state["all_messages"]

    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
