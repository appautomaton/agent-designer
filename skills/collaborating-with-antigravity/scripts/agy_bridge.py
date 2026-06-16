#!/usr/bin/env python3
"""
Antigravity CLI Bridge Script.

Wraps the Antigravity CLI (`agy --print`) to provide a JSON interface, live
stderr progress, and multi-turn continuity via SESSION_ID.

Antigravity CLI is Google's replacement for the (retiring) Gemini CLI. Two
quirks of `agy` v1.0.8 shape this bridge and are worked around here:

  1. Non-TTY stdout hang. `agy -p` writes nothing and hangs indefinitely when
     stdout is a pipe (even `--print-timeout` is ignored). We therefore run it
     under a pseudo-terminal (pty) so its TTY check passes, and enforce our own
     wall-clock kill. (Upstream: antigravity-cli issue #76.)
  2. No surfaced conversation ID. `agy -p` never prints the conversation ID and
     has no `--session-id`. We recover it from
     `~/.gemini/antigravity-cli/cache/last_conversations.json`, which maps the
     workspace abspath -> conversation UUID, and resume via `--conversation`.
     (Upstream: antigravity-cli issue #7.)

Because `agy` rewrites that cache on every run, concurrent runs would race ID
recovery; the bridge serializes with an advisory file lock. Verified against
`agy` (Antigravity CLI) v1.0.8 on Linux.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Control sequences agy emits even in print mode (no --no-color flag exists):
# CSI/OSC escapes, single-char escapes, and lone control bytes (keep \t \n).
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[=>]|[\x00-\x08\x0b\x0c\x0e-\x1f]")

CACHE_REL = ".gemini/antigravity-cli/cache/last_conversations.json"
CONV_DIR_REL = ".gemini/antigravity-cli/conversations"
OAUTH_TOKEN_REL = ".gemini/antigravity-cli/antigravity-oauth-token"


def emit_json(result: Dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)


def find_executable(name: str) -> str:
    found = shutil.which(name)
    return found if found else name


def list_models() -> Tuple[List[str], Optional[str]]:
    """Return (models, error) from `agy models`. Pipe-safe, unlike `agy -p`."""
    try:
        proc = subprocess.run(
            [find_executable("agy"), "models"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"Failed to run `agy models`: {exc}"
    if proc.returncode != 0:
        return [], proc.stderr.strip() or f"`agy models` exited {proc.returncode}."
    models = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return (models, None) if models else ([], "`agy models` returned no models.")


def parse_duration(text: str) -> Optional[float]:
    """Parse Go-style durations like '5m', '90s', '5m0s', or bare seconds."""
    text = text.strip().lower()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    total = 0.0
    matched = False
    for value, unit in re.findall(r"(\d+(?:\.\d+)?)([hms])", text):
        matched = True
        total += float(value) * {"h": 3600, "m": 60, "s": 1}[unit]
    return total if matched else None


def strip_ansi(raw: str) -> List[str]:
    """Strip control sequences and spinner redraws; return non-empty lines."""
    clean = ANSI_RE.sub("", raw)
    clean = re.sub(r"[ \t]*\r", "\n", clean)  # treat carriage returns as newlines
    return [line.rstrip() for line in clean.splitlines() if line.strip()]


def preflight_check(cd: Path, warnings: List[str]) -> Optional[str]:
    if os.name != "posix":
        return "agy_bridge requires a POSIX system (it allocates a pty); not supported on this OS."
    if shutil.which("agy") is None:
        return "Antigravity CLI not found in PATH. Install it (`curl -fsSL https://antigravity.google/cli/install.sh | bash`) and ensure `agy` is available."
    if not cd.exists():
        return f"Workspace root `{cd.absolute().as_posix()}` does not exist."
    if not cd.is_dir():
        return f"Workspace root `{cd.absolute().as_posix()}` is not a directory."
    if not (Path.home() / OAUTH_TOKEN_REL).is_file():
        warnings.append(
            "No Antigravity OAuth token found at ~/.gemini/antigravity-cli/. "
            "Run `agy` once and sign in with Google, or the call may hang on auth."
        )
    return None


def acquire_lock() -> Optional[Any]:
    """Serialize bridge runs so concurrent agy invocations don't race the cache."""
    try:
        import fcntl
    except ImportError:
        return None
    lock_dir = Path.home() / ".gemini/antigravity-cli/cache"
    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_path = lock_dir / ".agy_bridge.lock"
    except OSError:
        lock_path = Path("/tmp/.agy_bridge.lock")
    handle = open(lock_path, "w")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def release_lock(handle: Optional[Any]) -> None:
    if handle is None:
        return
    try:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass
    finally:
        handle.close()


def build_command(args: argparse.Namespace, prompt: str) -> List[str]:
    cmd = ["agy", "-p", prompt]
    if args.model:
        cmd.extend(["--model", args.model])
    if args.sandbox:
        cmd.append("--sandbox")
    if args.skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    for extra_dir in args.add_dir:
        cmd.extend(["--add-dir", extra_dir])
    if args.print_timeout:
        cmd.extend(["--print-timeout", args.print_timeout])
    if args.log_file:
        cmd.extend(["--log-file", args.log_file])
    if args.SESSION_ID:
        cmd.extend(["--conversation", args.SESSION_ID])
    elif args.continue_session:
        cmd.append("-c")
    return cmd


def run_agy_pty(
    cmd: List[str], cwd: Path, wall_timeout: float, start_time: float
) -> Tuple[str, int, bool]:
    """Run agy under a pty, forward cleaned output to stderr, return (raw, rc, timed_out)."""
    import pty

    def status(message: str) -> None:
        elapsed = time.time() - start_time
        print(f"[agy {elapsed:5.1f}s] {message}", file=sys.stderr, flush=True)

    resolved = cmd.copy()
    resolved[0] = find_executable(cmd[0])

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        resolved,
        stdin=subprocess.DEVNULL,
        stdout=slave,
        stderr=slave,
        cwd=str(cwd),
        close_fds=True,
        start_new_session=True,
    )
    os.close(slave)
    status(f"Started agy (pid {proc.pid}); waiting for response…")

    chunks: List[bytes] = []
    pending = ""  # partial line buffer for progress forwarding
    saw_output = False
    timed_out = False

    def forward(text: str, flush_all: bool = False) -> None:
        nonlocal pending
        pending += text
        *lines, pending = pending.split("\n")
        if flush_all and pending:
            lines.append(pending)
            pending = ""
        for line in lines:
            for clean in strip_ansi(line):
                status(clean[:200])

    while True:
        if time.time() - start_time > wall_timeout:
            timed_out = True
            status(f"Wall-clock timeout after {wall_timeout:g}s; killing agy")
            _killpg(proc)
            break
        try:
            ready, _, _ = select.select([master], [], [], 0.5)
        except (OSError, ValueError):
            break
        if master in ready:
            try:
                data = os.read(master, 65536)
            except OSError:  # EIO on Linux once the child exits
                break
            if not data:
                break
            if not saw_output:
                saw_output = True
                status("Receiving output…")
            chunks.append(data)
            forward(data.decode("utf-8", "replace"))
        elif proc.poll() is not None:
            try:  # drain anything left in the pty buffer
                while True:
                    data = os.read(master, 65536)
                    if not data:
                        break
                    chunks.append(data)
            except OSError:
                pass
            break

    forward("", flush_all=True)
    try:
        returncode = proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _killpg(proc)
        returncode = proc.wait()
    try:
        os.close(master)
    except OSError:
        pass

    raw = b"".join(chunks).decode("utf-8", "replace")
    return raw, returncode, timed_out


def _killpg(proc: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


def recover_session_id(cd: Path, start_time: float) -> Tuple[Optional[str], Optional[str]]:
    """Recover the conversation UUID for this workspace; return (id, db_path)."""
    cache_path = Path.home() / CACHE_REL
    cd_abs = str(cd.resolve())
    conv_id: Optional[str] = None
    try:
        mapping = json.loads(cache_path.read_text(encoding="utf-8"))
        if isinstance(mapping, dict):
            conv_id = mapping.get(cd_abs) or mapping.get(cd.absolute().as_posix())
    except (OSError, json.JSONDecodeError):
        pass

    conv_dir = Path.home() / CONV_DIR_REL
    if conv_id:
        db = conv_dir / f"{conv_id}.db"
        return conv_id, (str(db) if db.is_file() else None)

    # Fallback: newest .db touched since this run began.
    try:
        candidates = [
            p for p in conv_dir.glob("*.db") if p.stat().st_mtime >= start_time - 1
        ]
        if candidates:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            return newest.stem, str(newest)
    except OSError:
        pass
    return None, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Antigravity CLI (agy) Bridge")
    parser.add_argument("--PROMPT", default="", help="Instruction to send to agy. Use this or --prompt-file.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="Read the prompt from a file (avoids argv/shell-quoting limits).")
    parser.add_argument("--cd", type=Path, default=None, help="Workspace root for agy (required unless --list-models).")
    parser.add_argument("--list-models", action="store_true", help="Print models from `agy models` as JSON and exit (no prompt/cd needed).")
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument("--SESSION_ID", default="", help="Resume a conversation by ID (maps to `agy --conversation`).")
    session_group.add_argument("--continue", dest="continue_session", action="store_true", help="Continue the most recent conversation (maps to `agy -c`).")
    parser.add_argument("--model", default="", help='Model name from `agy models`, e.g. "Gemini 3.5 Flash (Low)" or "Claude Sonnet 4.6 (Thinking)".')
    parser.add_argument("--no-validate-model", action="store_true", help="Skip validating --model against `agy models` (agy does not validate; unknown names silently fall back to the default).")
    parser.add_argument("--sandbox", action=argparse.BooleanOptionalAction, default=True, help="Run agy with terminal restrictions (default: on). Use --no-sandbox to allow shell/tools.")
    parser.add_argument("--skip-permissions", action="store_true", help="Pass --dangerously-skip-permissions (auto-approve tools). Use only with explicit consent.")
    parser.add_argument("--add-dir", action="append", default=[], help="Add a directory to the workspace (repeatable).")
    parser.add_argument("--print-timeout", default="5m", help="agy print-mode wait, e.g. '5m' or '90s' (default 5m). Note: agy may ignore this; --timeout is the real cap.")
    parser.add_argument("--log-file", default="", help="Override agy's log file path.")
    parser.add_argument("--timeout", type=float, default=0, help="Bridge wall-clock kill, in seconds. Default: print-timeout + 120s buffer.")
    parser.add_argument("--return-all-messages", action="store_true", help="Include raw captured output and the conversation .db path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    warnings: List[str] = []

    if args.list_models:
        if shutil.which("agy") is None:
            emit_json({"success": False, "error": "Antigravity CLI not found in PATH. Install it and ensure `agy` is available."}, exit_code=1)
        models, err = list_models()
        if err:
            emit_json({"success": False, "error": err}, exit_code=1)
        emit_json({"success": True, "models": models})

    if args.cd is None:
        emit_json({"success": False, "error": "`--cd` is required (omit it only with --list-models)."}, exit_code=2)

    if args.PROMPT and args.prompt_file is not None:
        emit_json({"success": False, "error": "Use either `--PROMPT` or `--prompt-file`, not both."}, exit_code=2)
    if not args.PROMPT and args.prompt_file is None:
        emit_json({"success": False, "error": "Provide `--PROMPT` or `--prompt-file`."}, exit_code=2)
    if args.timeout < 0:
        emit_json({"success": False, "error": "`--timeout` must be zero or a positive number of seconds."}, exit_code=2)

    prompt = args.PROMPT
    if args.prompt_file is not None:
        if not args.prompt_file.is_file():
            emit_json({"success": False, "error": f"Prompt file not found: {args.prompt_file}"}, exit_code=2)
        prompt = args.prompt_file.read_text(encoding="utf-8")
    if not prompt.strip():
        emit_json({"success": False, "error": "Prompt is empty."}, exit_code=2)

    cd: Path = args.cd
    error = preflight_check(cd, warnings)
    if error:
        emit_json({"success": False, "error": error, "warnings": warnings}, exit_code=1)

    wall_timeout = args.timeout
    if not wall_timeout:
        wall_timeout = (parse_duration(args.print_timeout) or 300.0) + 120.0

    if args.skip_permissions:
        warnings.append("`--skip-permissions` auto-approves all agy tool actions without prompting.")

    if args.model and not args.no_validate_model:
        models, err = list_models()
        if err:
            warnings.append(f"Could not validate --model against `agy models` ({err}); proceeding.")
        elif args.model not in models:
            emit_json({
                "success": False,
                "error": (
                    f"Model {args.model!r} is not listed by `agy models`; agy would silently fall "
                    f"back to its default. Available: {models}. Use --no-validate-model to skip."
                ),
                "warnings": warnings,
            }, exit_code=2)

    cmd = build_command(args, prompt)
    start_time = time.time()

    lock = acquire_lock()
    try:
        raw, returncode, timed_out = run_agy_pty(cmd, cd.absolute(), wall_timeout, start_time)
        conv_id, db_path = recover_session_id(cd, start_time)
    except Exception as exc:  # pragma: no cover - defensive boundary
        release_lock(lock)
        emit_json({"success": False, "error": f"Failed to run agy: {exc}", "warnings": warnings}, exit_code=1)
    release_lock(lock)

    lines = strip_ansi(raw)
    agent_messages = "\n".join(lines).strip()

    errors: List[str] = []
    success = returncode == 0 and bool(agent_messages) and not timed_out
    if timed_out:
        errors.append(
            f"agy did not finish within {wall_timeout:g}s and was killed. "
            "agy hangs without a real terminal; the bridge runs it under a pty, "
            "but a long task may still exceed the wall-clock cap (raise --timeout)."
        )
    if returncode != 0 and not timed_out:
        errors.append(f"agy exited with non-zero status: {returncode}.")
    if not agent_messages and not errors:
        errors.append("No response captured from agy.")

    if conv_id:
        warnings.append(
            "SESSION_ID was recovered from last_conversations.json (agy does not surface it "
            "in print mode). Serialize concurrent bridge calls to keep recovery reliable."
        )
    elif success:
        warnings.append("Could not recover SESSION_ID; multi-turn resume will not be possible for this run.")

    result: Dict[str, Any] = {"success": success}
    if conv_id:
        result["SESSION_ID"] = conv_id
    result["agent_messages"] = agent_messages
    if args.model:
        result["model"] = args.model
    if warnings:
        result["warnings"] = warnings
    if not success:
        result["error"] = "\n".join(errors) or "agy did not return a usable response."
    if args.return_all_messages:
        result["raw_output"] = raw
        if db_path:
            result["db_path"] = db_path

    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
