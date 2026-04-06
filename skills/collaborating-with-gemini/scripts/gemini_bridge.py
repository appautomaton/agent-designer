#!/usr/bin/env python3
"""
Gemini Bridge Script for Codex Skills.

Wraps the Gemini CLI (-p headless mode) to provide a JSON-based interface
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
    resolved[0] = shutil.which("gemini") or cmd[0]

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
    parser = argparse.ArgumentParser(description="Gemini Bridge")
    parser.add_argument("--PROMPT", required=True, help="Instruction to send to Gemini.")
    parser.add_argument("--cd", required=True, type=Path, help="Workspace root for Gemini.")
    parser.add_argument("--SESSION_ID", default="", help="Resume the specified session.")
    parser.add_argument("--model", default="", help="Override the Gemini model.")
    parser.add_argument("--sandbox", action="store_true", help="Run in sandbox mode (blocks shell and file writes).")
    parser.add_argument(
        "--approval-mode",
        default="",
        choices=["", "default", "auto_edit", "yolo", "plan"],
        help="Gemini approval mode. Note: 'plan' does NOT reliably prevent writes.",
    )
    parser.add_argument(
        "--include-directories",
        action="append",
        default=[],
        help="Additional workspace directories (repeatable).",
    )
    parser.add_argument(
        "--return-all-messages",
        action="store_true",
        help="Include all messages (tool calls, traces) in output JSON.",
    )

    args = parser.parse_args()

    # --- Pre-flight checks ---
    if shutil.which("gemini") is None:
        print(json.dumps({
            "success": False,
            "error": "Gemini CLI not found in PATH. Install it and ensure `gemini` is available.",
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
    cmd = ["gemini", "-p", args.PROMPT, "-o", "stream-json"]

    if args.sandbox:
        cmd.append("--sandbox")
    if args.model:
        cmd.extend(["--model", args.model])
    if args.approval_mode:
        cmd.extend(["--approval-mode", args.approval_mode])
    if args.SESSION_ID:
        cmd.extend(["--resume", args.SESSION_ID])
    for d in args.include_directories:
        cmd.extend(["--include-directories", d])

    # --- Run ---
    stdout_lines, stderr_lines, returncode = run_command(cmd, cwd=cd.absolute().as_posix())

    # --- Parse output ---
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

            if obj.get("session_id") is not None:
                session_id = obj["session_id"]

            if obj.get("type") == "message" and obj.get("role") == "assistant":
                agent_messages += obj.get("content", "")

        except json.JSONDecodeError:
            err_message += "\n\n[json decode error] " + stripped
        except Exception as error:
            err_message += f"\n\n[unexpected error] {error}. Line: {stripped!r}"

    # --- Build result ---
    success = returncode == 0
    if not success and not err_message:
        err_message = f"Gemini CLI exited with non-zero status: {returncode}"

    if session_id is None:
        success = False
        err_message = "Failed to get `SESSION_ID` from the Gemini session.\n\n" + err_message

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
