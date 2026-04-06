#!/usr/bin/env python3
"""
Codex Bridge Script for Codex Skills.

Wraps the Codex CLI (exec mode) to provide a JSON-based interface
and multi-turn sessions via SESSION_ID.
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[List[str], List[str], int]:
    """Execute a command and return stdout/stderr as lists of lines."""
    resolved = cmd.copy()
    resolved[0] = shutil.which("codex") or cmd[0]

    process = subprocess.Popen(
        resolved,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        cwd=cwd,
    )
    stdout, stderr = process.communicate()
    stdout_lines = stdout.splitlines() if stdout else []
    stderr_lines = stderr.splitlines() if stderr else []
    return stdout_lines, stderr_lines, process.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex Bridge")
    parser.add_argument("--PROMPT", required=True, help="Instruction to send to Codex.")
    parser.add_argument("--cd", required=True, type=Path, help="Workspace root for Codex.")
    parser.add_argument("--SESSION_ID", default="", help="Resume a previous session by thread ID.")
    parser.add_argument("--last", action="store_true", help="Resume the most recent session.")
    parser.add_argument("--model", default="", help="Override the Codex model.")
    parser.add_argument(
        "--sandbox",
        default="read-only",
        choices=["read-only", "workspace-write", "danger-full-access"],
        help="Sandbox policy for model-generated commands. Default: read-only.",
    )
    parser.add_argument("--full-auto", action="store_true", help="Sandboxed automatic execution (workspace-write).")
    parser.add_argument("--image", action="append", default=[], help="Attach image files to the prompt (repeatable).")
    parser.add_argument("--add-dir", action="append", default=[], help="Additional writable directories (repeatable).")
    parser.add_argument("--skip-git-repo-check", action="store_true", help="Allow running outside a Git repository.")
    parser.add_argument("--ephemeral", action="store_true", help="Do not persist session to disk.")
    parser.add_argument(
        "--return-all-messages",
        action="store_true",
        help="Include all JSONL events (tool calls, usage) in output.",
    )

    args = parser.parse_args()

    # --- Pre-flight checks ---
    if shutil.which("codex") is None:
        print(json.dumps({
            "success": False,
            "error": "Codex CLI not found in PATH. Install it and ensure `codex` is available.",
        }, indent=2, ensure_ascii=False))
        return

    cd: Path = args.cd
    if not cd.exists():
        print(json.dumps({
            "success": False,
            "error": f"Workspace root `{cd.absolute().as_posix()}` does not exist.",
        }, indent=2, ensure_ascii=False))
        return

    # --- Build command ---
    if args.SESSION_ID or args.last:
        # Resume mode: codex exec resume [SESSION_ID] <prompt>
        cmd = ["codex", "exec", "resume"]
        if args.SESSION_ID:
            cmd.append(args.SESSION_ID)
        elif args.last:
            cmd.append("--last")
        cmd.append(args.PROMPT)
        cmd.append("--json")
    else:
        # New session: codex exec <prompt>
        cmd = ["codex", "exec", args.PROMPT, "--json", "-C", cd.absolute().as_posix(), "-s", args.sandbox]

    if args.model:
        cmd.extend(["-m", args.model])
    if args.full_auto:
        cmd.append("--full-auto")
    if args.skip_git_repo_check:
        cmd.append("--skip-git-repo-check")
    if args.ephemeral:
        cmd.append("--ephemeral")
    for img in args.image:
        cmd.extend(["-i", img])
    for d in args.add_dir:
        cmd.extend(["--add-dir", d])

    # --- Run ---
    cwd = cd.absolute().as_posix() if args.SESSION_ID or args.last else None
    stdout_lines, stderr_lines, returncode = run_command(cmd, cwd=cwd)

    # --- Parse JSONL output ---
    all_messages: List[Dict[str, Any]] = []
    agent_messages = ""
    err_message = ""
    session_id: Optional[str] = None

    for line in stdout_lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
            all_messages.append(obj)

            # Session ID from thread.started
            if obj.get("type") == "thread.started" and obj.get("thread_id"):
                session_id = obj["thread_id"]

            # Agent text from item.completed
            if obj.get("type") == "item.completed":
                item = obj.get("item", {})
                if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                    agent_messages += item["text"]

        except json.JSONDecodeError:
            err_message += "\n\n[json decode error] " + stripped
        except Exception as error:
            err_message += f"\n\n[unexpected error] {error}. Line: {stripped!r}"

    # --- Build result ---
    success = returncode == 0
    if not success and not err_message:
        err_message = f"Codex CLI exited with non-zero status: {returncode}"

    if session_id is None and not args.ephemeral:
        success = False
        err_message = "Failed to get `SESSION_ID` from the Codex session.\n\n" + err_message

    stderr_text = "\n".join(stderr_lines).strip()
    if stderr_text:
        err_message = (err_message + "\n\n" if err_message else "") + "[stderr]\n" + stderr_text

    result: Dict[str, Any] = {"success": success}
    if session_id is not None:
        result["SESSION_ID"] = session_id
    result["agent_messages"] = agent_messages
    if not success:
        result["error"] = err_message
    if args.return_all_messages:
        result["all_messages"] = all_messages

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
