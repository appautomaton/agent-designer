#!/usr/bin/env python3
"""
Codex Bridge Script for Codex Skills.

Wraps Codex CLI exec mode to provide a JSON interface and multi-turn
continuity via SESSION_ID.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


SANDBOX_MODES = ("read-only", "workspace-write", "danger-full-access")
PATH_WARNING_PREFIX = "WARNING: proceeding, even though we could not update PATH:"
STDIN_INFO_PREFIX = "Reading additional input from stdin..."
APPROVAL_POLICIES = ("untrusted", "on-failure", "on-request", "never")


def emit_json(result: Dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)


def find_executable(name: str) -> str:
    """Locate an executable while handling Windows npm shims."""
    found = shutil.which(name)
    if found:
        if os.name == "nt" and not Path(found).suffix:
            for ext in (".cmd", ".bat", ".exe"):
                alt = Path(found).parent / f"{name}{ext}"
                if alt.is_file():
                    return str(alt)
        return found
    if os.name == "nt":
        for env_var in ("APPDATA", "LOCALAPPDATA"):
            base = os.environ.get(env_var, "")
            if base:
                for ext in (".cmd", ".bat", ".exe"):
                    candidate = Path(base) / "npm" / f"{name}{ext}"
                    if candidate.is_file():
                        return str(candidate)
    return name


def preflight_check(cd: Path) -> Optional[str]:
    if shutil.which("codex") is None:
        return "Codex CLI not found in PATH. Install it and ensure `codex` is available."
    if not cd.exists():
        return f"Workspace root `{cd.absolute().as_posix()}` does not exist."
    if not cd.is_dir():
        return f"Workspace root `{cd.absolute().as_posix()}` is not a directory."

    has_env_key = bool(os.environ.get("OPENAI_API_KEY"))
    has_auth_file = Path.home().joinpath(".codex", "auth.json").is_file()
    if not has_env_key and not has_auth_file:
        return "No Codex auth found. Run `codex login` or export `OPENAI_API_KEY`."
    return None


def normalize_sandbox(args: argparse.Namespace, warnings: List[str]) -> str:
    sandbox = args.sandbox
    if args.full_auto:
        sandbox = "workspace-write"
        warnings.append(
            "`--full-auto` is deprecated for this bridge and is not forwarded to Codex; "
            "using `--sandbox workspace-write` instead."
        )
    return sandbox


def build_command(args: argparse.Namespace, cd: Path, sandbox: str, prompt_arg: str) -> List[str]:
    """Build a Codex CLI command compatible with current `codex exec`."""
    cmd = ["codex"]
    if args.search:
        cmd.append("--search")
    if args.ask_for_approval:
        cmd.extend(["-a", args.ask_for_approval])

    cmd.extend(["exec", "--json", "-C", cd.absolute().as_posix(), "-s", sandbox])

    for add_dir in args.add_dir:
        cmd.extend(["--add-dir", add_dir])
    if args.profile:
        cmd.extend(["-p", args.profile])
    if args.oss:
        cmd.append("--oss")
    if args.local_provider:
        cmd.extend(["--local-provider", args.local_provider])
    if args.color:
        cmd.extend(["--color", args.color])

    if args.SESSION_ID or args.last:
        cmd.append("resume")

    if args.model:
        cmd.extend(["-m", args.model])
    if args.bypass_sandbox:
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    if args.bypass_hook_trust:
        cmd.append("--dangerously-bypass-hook-trust")
    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if args.ephemeral:
        cmd.append("--ephemeral")
    if args.ignore_user_config:
        cmd.append("--ignore-user-config")
    if args.ignore_rules:
        cmd.append("--ignore-rules")
    if args.strict_config:
        cmd.append("--strict-config")
    if args.output_schema:
        cmd.extend(["--output-schema", str(args.output_schema)])
    if args.output_last_message:
        cmd.extend(["-o", str(args.output_last_message)])
    for img in args.image:
        cmd.extend(["-i", img])
    if args.network:
        cmd.extend(["-c", "sandbox_workspace_write.network_access=true"])
    for cfg in args.config:
        cmd.extend(["-c", cfg])
    for feature in args.enable:
        cmd.extend(["--enable", feature])
    for feature in args.disable:
        cmd.extend(["--disable", feature])

    if args.SESSION_ID or args.last:
        if args.resume_all:
            cmd.append("--all")
        if args.last:
            cmd.append("--last")
        elif args.SESSION_ID:
            cmd.append(args.SESSION_ID)

    cmd.extend(["--", prompt_arg])
    return cmd


def stream_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    stdin_file: Optional[Path] = None,
    timeout_seconds: float = 0,
) -> Generator[str, None, int]:
    """Execute a command and yield stdout JSONL lines while forwarding stderr progress."""
    resolved = cmd.copy()
    resolved[0] = find_executable(cmd[0])

    if os.name == "nt" and Path(resolved[0]).suffix.lower() in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        resolved = [comspec, "/d", "/s", "/c", " ".join(f'"{arg}"' for arg in resolved)]

    stdin_handle = None
    try:
        stdin = subprocess.DEVNULL
        if stdin_file is not None:
            stdin_handle = stdin_file.open("r", encoding="utf-8", errors="replace")
            stdin = stdin_handle

        proc = subprocess.Popen(
            resolved,
            shell=False,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd is not None else None,
        )
    finally:
        if stdin_handle is not None:
            stdin_handle.close()

    out_q: queue.Queue[Optional[str]] = queue.Queue()
    started_at = time.time()

    def read_stdout() -> None:
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            stripped = line.strip()
            if stripped:
                out_q.put(stripped)
                try:
                    if json.loads(stripped).get("type") == "turn.completed":
                        time.sleep(0.3)
                        proc.terminate()
                        break
                except (json.JSONDecodeError, AttributeError, TypeError):
                    pass
        proc.stdout.close()
        out_q.put(None)

    def read_stderr() -> None:
        assert proc.stderr is not None
        for line in iter(proc.stderr.readline, ""):
            text = line.rstrip()
            if text and not text.startswith(PATH_WARNING_PREFIX) and not text.startswith(STDIN_INFO_PREFIX):
                print(f"[codex stderr] {text}", file=sys.stderr, flush=True)
        proc.stderr.close()

    t_out = threading.Thread(target=read_stdout, daemon=True)
    t_err = threading.Thread(target=read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    while True:
        if timeout_seconds and time.time() - started_at > timeout_seconds:
            print(
                f"[codex stderr] timeout after {timeout_seconds:g}s; terminating Codex",
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


def summarize_event(
    event: Dict[str, Any],
    all_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    start_time: float,
) -> None:
    all_messages.append(event)

    def status(message: str) -> None:
        elapsed = time.time() - start_time
        print(f"[codex {elapsed:5.1f}s] {message}", file=sys.stderr, flush=True)

    event_type = event.get("type", "")
    if event_type == "thread.started" and event.get("thread_id"):
        state["session_id"] = event["thread_id"]
        status(f"Session: {event['thread_id']}")
    elif event_type == "turn.started":
        status("Codex is working...")
    elif event_type == "turn.completed":
        state["turn_completed"] = True
        usage = event.get("usage", {})
        if usage:
            state["usage"] = usage
        tokens_in = usage.get("input_tokens")
        tokens_out = usage.get("output_tokens")
        if tokens_in is not None or tokens_out is not None:
            status(f"Done. Tokens: {tokens_in or 0} in / {tokens_out or 0} out")
        else:
            status("Done.")

    item = event.get("item", {})
    if isinstance(item, dict):
        item_type = item.get("type", "")
        if event_type == "item.completed" and item_type:
            counts = state["activity_counts"]
            counts[item_type] = counts.get(item_type, 0) + 1
            item_type_lower = str(item_type).lower()
            if "web_search" in item_type_lower or "web-search" in item_type_lower:
                state["web_searches"] += 1
                status("Web search completed")
            elif "mcp" in item_type_lower:
                state["mcp_tools_ran"] += 1
                status(f"MCP activity: {item_type}")
            elif "file" in item_type_lower and (
                "change" in item_type_lower or "patch" in item_type_lower or "edit" in item_type_lower
            ):
                if str(item.get("status", "")).lower() == "failed":
                    state["files_failed"] += 1
                    status(f"File activity FAILED: {item_type}")
                else:
                    state["files_changed"] += 1
                    status(f"File activity: {item_type}")
            elif "plan" in item_type_lower or item_type_lower == "todo_list":
                state["plan_updates"] += 1
                status("Plan updated")

        if item_type == "agent_message" and isinstance(item.get("text"), str):
            state["agent_messages"] += item["text"]
            preview = item["text"][:80].replace("\n", " ")
            if preview:
                status(f"Response: {preview}{'...' if len(item['text']) > 80 else ''}")
        elif item_type == "command_execution":
            command = str(item.get("command", ""))
            exit_code = item.get("exit_code")
            if exit_code is not None:
                state["commands_ran"] += 1
                state["command_exit_codes"].append(exit_code)
                if exit_code != 0 or str(item.get("status", "")).lower() in ("failed", "declined"):
                    state["commands_failed"] += 1
                status(f"Ran: {command[:60]} (exit {exit_code})")
            elif command:
                status(f"Running: {command[:60]}")

    if "fail" in event_type or "error" in event_type:
        message = ""
        error_obj = event.get("error")
        if isinstance(error_obj, dict):
            message = str(error_obj.get("message", ""))
        message = message or str(event.get("message", ""))
        if message and not re.match(r"^Reconnecting\.\.\.\s+\d+/\d+$", message):
            state["errors"].append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex Bridge")
    parser.add_argument("--PROMPT", default="", help="Instruction to send to Codex.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="Read the Codex prompt from a file.")
    parser.add_argument(
        "--stdin-file",
        type=Path,
        default=None,
        help="Pipe a file to Codex stdin as additional context when --PROMPT is used.",
    )
    parser.add_argument("--cd", required=True, type=Path, help="Workspace root for Codex.")
    parser.add_argument("--SESSION_ID", default="", help="Resume a previous session by thread ID.")
    parser.add_argument("--last", action="store_true", help="Resume the most recent session.")
    parser.add_argument(
        "--resume-all",
        action="store_true",
        help="With --SESSION_ID or --last, disable Codex's cwd filtering while selecting sessions.",
    )
    parser.add_argument("--model", default="", help="Override the Codex model.")
    parser.add_argument(
        "--sandbox",
        default="read-only",
        choices=SANDBOX_MODES,
        help="Sandbox policy for model-generated commands. Default: read-only.",
    )
    parser.add_argument(
        "--full-auto",
        action="store_true",
        help="Deprecated compatibility alias: use workspace-write sandbox; not forwarded to Codex.",
    )
    parser.add_argument("--image", action="append", default=[], help="Attach image files to the prompt.")
    parser.add_argument("--add-dir", action="append", default=[], help="Additional writable directories.")
    parser.add_argument(
        "--skip-git-repo-check",
        action="store_true",
        default=True,
        help="Allow running outside a Git repo. Default: on for parity with codex-collab.",
    )
    parser.add_argument(
        "--require-git-repo",
        action="store_true",
        help="Do not pass --skip-git-repo-check to Codex.",
    )
    parser.add_argument("--ephemeral", action="store_true", help="Do not persist session files.")
    parser.add_argument("--profile", default="", help="Config profile from CODEX_HOME.")
    parser.add_argument(
        "--bypass-sandbox",
        action="store_true",
        help="Forward Codex's dangerous bypass flag. Use only with explicit user consent.",
    )
    parser.add_argument(
        "--bypass-hook-trust",
        action="store_true",
        help="Forward Codex's dangerous hook-trust bypass flag. Use only with explicit user consent.",
    )
    parser.add_argument(
        "--search",
        action="store_true",
        help="Enable live web search by forwarding top-level `codex --search` before exec.",
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Allow outbound shell network inside the workspace-write sandbox "
        "(forwards `-c sandbox_workspace_write.network_access=true`).",
    )
    parser.add_argument(
        "-a",
        "--ask-for-approval",
        choices=APPROVAL_POLICIES,
        default="",
        help="Approval policy for model-generated commands.",
    )
    parser.add_argument("--oss", action="store_true", help="Use Codex open-source provider mode.")
    parser.add_argument("--local-provider", default="", help="Local OSS provider such as lmstudio or ollama.")
    parser.add_argument("--ignore-user-config", action="store_true", help="Do not load CODEX_HOME config.")
    parser.add_argument("--ignore-rules", action="store_true", help="Do not load user/project execpolicy rules.")
    parser.add_argument("--strict-config", action="store_true", help="Error on unrecognized config fields.")
    parser.add_argument("--output-schema", type=Path, default=None, help="JSON Schema file for final response.")
    parser.add_argument("-o", "--output-last-message", type=Path, default=None, help="Write final message to file.")
    parser.add_argument(
        "--color",
        choices=("always", "never", "auto"),
        default="",
        help="Codex output color mode.",
    )
    parser.add_argument(
        "-c",
        "--config",
        action="append",
        default=[],
        metavar="key=value",
        help="Override a Codex config value. Repeatable.",
    )
    parser.add_argument("--enable", action="append", default=[], metavar="FEATURE", help="Enable a feature.")
    parser.add_argument("--disable", action="append", default=[], metavar="FEATURE", help="Disable a feature.")
    parser.add_argument(
        "--return-all-messages",
        action="store_true",
        help="Include all JSONL events in output.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0,
        help="Terminate Codex after this many seconds. Default: no bridge timeout.",
    )
    return parser.parse_args()


def resolve_prompt_input(args: argparse.Namespace) -> Tuple[str, Optional[Path]]:
    if args.PROMPT and args.prompt_file:
        emit_json({"success": False, "error": "Use either `--PROMPT` or `--prompt-file`, not both."}, exit_code=2)
    if args.prompt_file and args.stdin_file:
        emit_json({"success": False, "error": "Use either `--prompt-file` or `--stdin-file`, not both."}, exit_code=2)
    if not args.PROMPT and args.prompt_file is None:
        emit_json({"success": False, "error": "Provide `--PROMPT` or `--prompt-file`."}, exit_code=2)

    stdin_file: Optional[Path] = None
    prompt_arg = args.PROMPT
    if args.prompt_file is not None:
        if not args.prompt_file.is_file():
            emit_json({"success": False, "error": f"Prompt file not found: {args.prompt_file}"}, exit_code=2)
        prompt_arg = "-"
        stdin_file = args.prompt_file
    elif args.stdin_file is not None:
        if not args.stdin_file.is_file():
            emit_json({"success": False, "error": f"Stdin context file not found: {args.stdin_file}"}, exit_code=2)
        stdin_file = args.stdin_file

    if os.name == "nt" and prompt_arg != "-":
        prompt_arg = prompt_arg.replace("\n", "\\n").replace("\r", "\\r")
    return prompt_arg, stdin_file


def main() -> None:
    args = parse_args()
    warnings: List[str] = []

    if args.SESSION_ID and args.last:
        emit_json({"success": False, "error": "Use either `--SESSION_ID` or `--last`, not both."}, exit_code=2)
    if args.resume_all and not (args.SESSION_ID or args.last):
        emit_json({"success": False, "error": "`--resume-all` requires `--SESSION_ID` or `--last`."}, exit_code=2)
    if args.timeout < 0:
        emit_json({"success": False, "error": "`--timeout` must be zero or a positive number of seconds."}, exit_code=2)
    if args.require_git_repo:
        args.skip_git_repo_check = False
    if args.ask_for_approval == "on-failure":
        warnings.append("`--ask-for-approval on-failure` is deprecated by Codex; prefer `on-request` or `never`.")

    cd: Path = args.cd
    error = preflight_check(cd)
    if error:
        emit_json({"success": False, "error": error}, exit_code=1)

    sandbox = normalize_sandbox(args, warnings)
    if args.bypass_sandbox:
        warnings.append("Forwarding Codex dangerous bypass flag; this skips approvals and sandboxing.")
    if args.bypass_hook_trust:
        warnings.append("Forwarding Codex dangerous hook-trust bypass flag.")
    if args.network and sandbox != "workspace-write":
        warnings.append(
            "`--network` only affects the workspace-write sandbox; "
            f"it has no effect under `{sandbox}`."
        )

    prompt_arg, stdin_file = resolve_prompt_input(args)
    cmd = build_command(args, cd, sandbox, prompt_arg)
    cwd = cd.absolute() if args.SESSION_ID or args.last else None

    all_messages: List[Dict[str, Any]] = []
    state: Dict[str, Any] = {
        "agent_messages": "",
        "commands_ran": 0,
        "commands_failed": 0,
        "command_exit_codes": [],
        "errors": [],
        "session_id": None,
        "turn_completed": False,
        "activity_counts": {},
        "files_changed": 0,
        "files_failed": 0,
        "mcp_tools_ran": 0,
        "plan_updates": 0,
        "usage": {},
        "web_searches": 0,
    }
    start_time = time.time()
    returncode = 1

    try:
        generator = stream_command(cmd, cwd=cwd, stdin_file=stdin_file, timeout_seconds=args.timeout)
        while True:
            try:
                line = next(generator)
            except StopIteration as finished:
                returncode = int(finished.value or 0)
                break

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                state["errors"].append(f"[json decode error] {line}")
                continue
            except Exception as exc:  # pragma: no cover - defensive boundary
                state["errors"].append(f"[unexpected parse error] {exc}. Line: {line!r}")
                continue
            summarize_event(event, all_messages, state, start_time)
    except Exception as exc:
        emit_json({"success": False, "error": f"Failed to run Codex CLI: {exc}", "warnings": warnings}, exit_code=1)

    exit_codes = state["command_exit_codes"]
    if (
        sandbox in ("read-only", "workspace-write")
        and not args.bypass_sandbox
        and exit_codes
        and 182 in exit_codes
        and all(code != 0 for code in exit_codes)
    ):
        warnings.append(
            "Every sandboxed command failed and at least one exited with code 182. "
            "Codex's sandbox is likely unsupported on this host (common under containers, "
            "PRoot, and older WSL), so Codex could not actually run commands; treat "
            "`agent_messages` as unverified. Probe with `codex sandbox -- true` and see "
            "the skill's Safety model section for options."
        )

    success = returncode == 0 or bool(state["turn_completed"])
    if state["session_id"] is None and not args.ephemeral:
        success = False
        state["errors"].append("Failed to get `SESSION_ID` from the Codex session.")
    if not state["agent_messages"] and state["commands_ran"] == 0:
        success = False
        state["errors"].append("Failed to get agent output from Codex.")
    if returncode != 0 and not state["turn_completed"]:
        state["errors"].append(f"Codex CLI exited with non-zero status: {returncode}")
    if args.timeout and returncode == 124 and not state["turn_completed"]:
        state["errors"].append(f"Codex may have timed out after {args.timeout:g} seconds.")

    result: Dict[str, Any] = {"success": success}
    if state["session_id"] is not None:
        result["SESSION_ID"] = state["session_id"]
    result["agent_messages"] = state["agent_messages"]
    if state["commands_ran"]:
        result["commands_ran"] = state["commands_ran"]
    for key in ("commands_failed", "web_searches", "mcp_tools_ran", "files_changed", "files_failed", "plan_updates"):
        if state[key]:
            result[key] = state[key]
    if state["usage"]:
        result["usage"] = state["usage"]
    if state["activity_counts"]:
        result["activity_counts"] = state["activity_counts"]
    if warnings:
        result["warnings"] = warnings
    if not success:
        result["error"] = "\n".join(str(err) for err in state["errors"] if err) or "No response from Codex."
    if args.return_all_messages:
        result["all_messages"] = all_messages

    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
