#!/usr/bin/env python3
"""
Claude Code Bridge Script.

Wraps the Claude Code CLI (`claude --print`) to provide a JSON interface,
live stderr progress, multi-turn sessions via SESSION_ID, and structured
result telemetry (termination reason, cost, tokens, turns).

Verified against `claude` (Claude Code) CLI v2.1.201.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional


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
    if shutil.which("claude") is None:
        return "Claude Code CLI not found in PATH. Install it and ensure `claude` is available."
    if not cd.exists():
        return f"Workspace root `{cd.absolute().as_posix()}` does not exist."
    if not cd.is_dir():
        return f"Workspace root `{cd.absolute().as_posix()}` is not a directory."
    return None


def extract_assistant_text(message: Any) -> str:
    """Pull concatenated text blocks from an assistant message object."""
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts: List[str] = []
    if isinstance(content, list):
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
            ):
                parts.append(block["text"])
    return "".join(parts)


def stream_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_seconds: float = 0,
    stdin_file: Optional[Path] = None,
) -> Generator[str, None, int]:
    """Execute a command and yield stdout lines while forwarding stderr progress."""
    resolved = cmd.copy()
    resolved[0] = find_executable(cmd[0])

    if os.name == "nt" and Path(resolved[0]).suffix.lower() in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        resolved = [comspec, "/d", "/s", "/c", " ".join(f'"{arg}"' for arg in resolved)]

    stdin_handle = None
    try:
        stdin_target: Any = subprocess.DEVNULL
        if stdin_file is not None:
            stdin_handle = stdin_file.open("r", encoding="utf-8", errors="replace")
            stdin_target = stdin_handle
        proc = subprocess.Popen(
            resolved,
            shell=False,
            stdin=stdin_target,
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
            text = line.rstrip()
            if text:
                print(f"[claude stderr] {text}", file=sys.stderr, flush=True)
        proc.stderr.close()

    t_out = threading.Thread(target=read_stdout, daemon=True)
    t_err = threading.Thread(target=read_stderr, daemon=True)
    t_out.start()
    t_err.start()

    while True:
        if timeout_seconds and time.time() - started_at > timeout_seconds:
            print(
                f"[claude] timeout after {timeout_seconds:g}s; terminating Claude Code",
                file=sys.stderr,
                flush=True,
            )
            proc.kill()
            return proc.wait()
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


def apply_result_event(event: Dict[str, Any], state: Dict[str, Any]) -> None:
    """Copy fields from a `type:result` event into bridge state."""
    state["subtype"] = event.get("subtype")
    state["is_error"] = bool(event.get("is_error"))
    if isinstance(event.get("result"), str):
        state["result_text"] = event["result"]
    state["total_cost_usd"] = event.get("total_cost_usd")
    state["usage"] = event.get("usage") or {}
    state["num_turns"] = event.get("num_turns")
    state["permission_denials"] = event.get("permission_denials") or []
    state["terminal_reason"] = event.get("terminal_reason")
    state["stop_reason"] = event.get("stop_reason")
    state["duration_ms"] = event.get("duration_ms")
    model_usage = event.get("modelUsage")
    if isinstance(model_usage, dict) and model_usage and not state.get("model"):
        state["model"] = next(iter(model_usage))
    if event.get("structured_output") is not None:
        state["structured_output"] = event.get("structured_output")


def summarize_event(
    event: Dict[str, Any],
    all_messages: List[Dict[str, Any]],
    state: Dict[str, Any],
    start_time: float,
) -> None:
    """Update state from a stream-json event and emit a stderr progress line."""
    all_messages.append(event)

    def status(message: str) -> None:
        elapsed = time.time() - start_time
        print(f"[claude {elapsed:5.1f}s] {message}", file=sys.stderr, flush=True)

    if event.get("session_id") and not state["session_id"]:
        state["session_id"] = event["session_id"]

    etype = event.get("type", "")

    if etype == "system":
        subtype = event.get("subtype", "")
        if subtype == "init":
            state["session_id"] = event.get("session_id") or state["session_id"]
            state["model"] = event.get("model")
            status(f"Session {state['session_id']} · model {event.get('model', '?')}")
        elif subtype == "api_retry":
            status(f"API retry {event.get('attempt')}/{event.get('max_retries')} ({event.get('error', '?')})")
        elif subtype == "compact_boundary":
            status("Context compacted")

    elif etype == "assistant":
        message = event.get("message", {})
        text = extract_assistant_text(message)
        if text:
            state["agent_messages"] += text
            preview = text[:80].replace("\n", " ")
            status(f"Response: {preview}{'…' if len(text) > 80 else ''}")
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    state["tools_used"] += 1
                    name = str(block.get("name", "?"))
                    state["tool_counts"][name] = state["tool_counts"].get(name, 0) + 1
                    status(f"Tool: {name}")

    elif etype == "user":
        content = event.get("message", {}).get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                    state["tools_failed"] += 1
                    body = block.get("content")
                    text = body if isinstance(body, str) else ""
                    if isinstance(body, list):
                        text = " ".join(
                            part.get("text", "") for part in body if isinstance(part, dict)
                        )
                    preview = text.strip().replace("\n", " ")[:80]
                    status(f"Tool error: {preview}" if preview else "Tool error")

    elif etype == "rate_limit_event":
        info = event.get("rate_limit_info", {})
        if isinstance(info, dict) and info.get("status") and info.get("status") != "allowed":
            state["rate_limited"] = True
            status(f"Rate limit: {info.get('status')} ({info.get('rateLimitType', '?')})")

    elif etype == "result":
        apply_result_event(event, state)
        cost = state["total_cost_usd"]
        cost_s = f"${cost:.4f}" if isinstance(cost, (int, float)) else "?"
        usage = state["usage"] or {}
        status(
            f"Done · {state['subtype']} · {cost_s} · "
            f"{usage.get('input_tokens', 0) or 0} in / {usage.get('output_tokens', 0) or 0} out · "
            f"{state['num_turns'] or 0} turns"
        )

    if "error" in etype and etype != "result":
        message = ""
        error_obj = event.get("error")
        if isinstance(error_obj, dict):
            message = str(error_obj.get("message", ""))
        message = message or str(event.get("message", ""))
        if message:
            state["errors"].append(message)


def parse_json_blob(raw_lines: List[str], all_messages: List[Dict[str, Any]], state: Dict[str, Any]) -> None:
    """Parse non-streaming `--output-format json` output (a single result object)."""
    raw = "\n".join(raw_lines).strip()
    if not raw:
        state["errors"].append("No output received from Claude Code.")
        return
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        state["errors"].append(f"Failed to parse JSON output: {error}")
        return

    objects = parsed if isinstance(parsed, list) else [parsed]
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        all_messages.append(obj)
        if obj.get("session_id") and not state["session_id"]:
            state["session_id"] = obj["session_id"]
        if obj.get("type") == "result" or "subtype" in obj:
            apply_result_event(obj, state)
        elif obj.get("type") == "assistant":
            state["agent_messages"] += extract_assistant_text(obj.get("message", {}))


def build_command(args: argparse.Namespace, prompt_arg: Optional[str]) -> List[str]:
    cmd = ["claude", "--print"]
    if prompt_arg is not None:
        cmd.append(prompt_arg)
    cmd.extend(["--output-format", args.output_format, "--input-format", args.input_format])

    if args.include_partial_messages:
        cmd.append("--include-partial-messages")
    if args.output_format == "stream-json" or args.verbose:
        cmd.append("--verbose")

    if args.model:
        cmd.extend(["--model", args.model])
    if args.effort:
        cmd.extend(["--effort", args.effort])
    if args.bare:
        cmd.append("--bare")
    if args.safe_mode:
        cmd.append("--safe-mode")
    if args.fallback_model:
        cmd.extend(["--fallback-model", args.fallback_model])
    if args.max_budget_usd:
        cmd.extend(["--max-budget-usd", args.max_budget_usd])
    if args.max_turns:
        cmd.extend(["--max-turns", args.max_turns])
    if args.json_schema:
        cmd.extend(["--json-schema", args.json_schema])

    if args.continue_session:
        cmd.append("--continue")
    if args.SESSION_ID:
        cmd.extend(["--resume", args.SESSION_ID])
    if args.session_id:
        cmd.extend(["--session-id", args.session_id])
    if args.fork_session:
        cmd.append("--fork-session")
    if args.no_session_persistence:
        cmd.append("--no-session-persistence")

    for extra_dir in args.add_dir:
        cmd.extend(["--add-dir", extra_dir])
    if args.system_prompt:
        cmd.extend(["--system-prompt", args.system_prompt])
    if args.system_prompt_file:
        cmd.extend(["--system-prompt-file", args.system_prompt_file])
    if args.append_system_prompt:
        cmd.extend(["--append-system-prompt", args.append_system_prompt])
    if args.append_system_prompt_file:
        cmd.extend(["--append-system-prompt-file", args.append_system_prompt_file])

    for tool in args.allowed_tools:
        cmd.extend(["--allowedTools", tool])
    if args.tools:
        cmd.extend(["--tools", args.tools])
    for tool in args.disallowed_tools:
        cmd.extend(["--disallowedTools", tool])

    if args.permission_mode:
        cmd.extend(["--permission-mode", args.permission_mode])
    if args.permission_prompt_tool:
        cmd.extend(["--permission-prompt-tool", args.permission_prompt_tool])

    for cfg in args.mcp_config:
        cmd.extend(["--mcp-config", cfg])
    if args.strict_mcp_config:
        cmd.append("--strict-mcp-config")
    for settings in args.settings:
        cmd.extend(["--settings", settings])
    if args.setting_sources:
        cmd.extend(["--setting-sources", args.setting_sources])
    if args.agent:
        cmd.extend(["--agent", args.agent])
    if args.agents:
        cmd.extend(["--agents", args.agents])

    return cmd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Claude Code Bridge")
    parser.add_argument("--PROMPT", default="", help="Instruction to send to claude. Use this or --prompt-file.")
    parser.add_argument("--prompt-file", type=Path, default=None, help="Read the prompt from a file and pipe it to claude via stdin (avoids argv/shell-quoting limits).")
    parser.add_argument("--cd", required=True, type=Path, help="Set the workspace root for claude before executing the task.")
    session_group = parser.add_mutually_exclusive_group()
    session_group.add_argument("--SESSION_ID", default="", help="Resume the specified session of claude.")
    session_group.add_argument("--session-id", dest="session_id", default="", help="Use a specific session ID (UUID).")
    session_group.add_argument("--continue", dest="continue_session", action="store_true", help="Continue the most recent session.")
    parser.add_argument("--fork-session", action="store_true", help="Fork session when resuming/continuing.")
    parser.add_argument("--no-session-persistence", action="store_true", help="Disable session persistence (print mode only).")
    parser.add_argument("--model", default="", help="Model override (alias like 'sonnet'/'opus', or a full model name).")
    parser.add_argument("--effort", default="", choices=["", "low", "medium", "high", "xhigh", "max"], help="Reasoning effort level (model-dependent).")
    parser.add_argument("--bare", action="store_true", help="Minimal mode: skip hooks/skills/plugins/MCP/CLAUDE.md/keychain. Requires ANTHROPIC_API_KEY or apiKeyHelper.")
    parser.add_argument("--safe-mode", dest="safe_mode", action="store_true", help="Disable customizations (CLAUDE.md/skills/plugins/hooks/MCP) but keep normal auth/model/permissions.")
    parser.add_argument("--fallback-model", default="", help="Fallback model(s), comma-separated, when the default is overloaded.")
    parser.add_argument("--max-budget-usd", default="", help="Max USD budget for the call (print mode only).")
    parser.add_argument("--max-turns", default="", help="Maximum agentic turns before stopping (print mode only).")
    parser.add_argument("--json-schema", default="", help="JSON schema for structured output (validated post-generation, not constrained decoding).")
    parser.add_argument("--input-format", default="text", choices=["text", "stream-json"], help="Claude input format.")
    parser.add_argument("--add-dir", action="append", default=[], help="Add additional working directories.")
    parser.add_argument("--append-system-prompt", default="", help="Append text to the default system prompt.")
    parser.add_argument("--append-system-prompt-file", default="", help="Append a file's contents to the default system prompt.")
    parser.add_argument("--system-prompt", default="", help="Replace the system prompt for the session.")
    parser.add_argument("--system-prompt-file", default="", help="Replace the system prompt with a file's contents.")
    parser.add_argument("--allowed-tools", action="append", default=[], help="Tools to allow without prompting.")
    parser.add_argument("--disallowed-tools", action="append", default=[], help="Tools to remove from context.")
    parser.add_argument("--tools", default="", help='Built-in tools to enable: "" (none), "default", or e.g. "Read,Glob,Grep".')
    parser.add_argument("--permission-mode", default="", help="Permission mode: plan/manual/acceptEdits/auto/dontAsk/bypassPermissions (CLI >=2.1.201 names the old 'default' mode 'manual'; both parse).")
    parser.add_argument("--permission-prompt-tool", default="", help="MCP tool to handle permission prompts.")
    parser.add_argument("--mcp-config", action="append", default=[], help="Load MCP servers from JSON files or strings.")
    parser.add_argument("--strict-mcp-config", action="store_true", help="Only use MCP servers from --mcp-config.")
    parser.add_argument("--settings", action="append", default=[], help="Load settings from JSON files or strings.")
    parser.add_argument("--setting-sources", default="", help="Comma-separated list of setting sources.")
    parser.add_argument("--agent", default="", help="Agent name to use for the session.")
    parser.add_argument("--agents", default="", help="JSON defining custom agents.")
    parser.add_argument("--output-format", default="stream-json", choices=["text", "json", "stream-json"], help="Claude output format.")
    parser.add_argument("--include-partial-messages", action="store_true", help="Include partial streaming events.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose CLI output (required for stream-json).")
    parser.add_argument(
        "--timeout",
        type=float,
        default=0,
        help="Terminate Claude after this many seconds. Default: no bridge timeout.",
    )
    parser.add_argument(
        "--return-all-messages",
        action="store_true",
        help="Return all messages (e.g. tool calls, traces) from the claude session.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.timeout < 0:
        emit_json({"success": False, "error": "`--timeout` must be zero or a positive number of seconds."}, exit_code=2)

    # Resolve the prompt source: exactly one of --PROMPT / --prompt-file.
    if args.PROMPT and args.prompt_file is not None:
        emit_json({"success": False, "error": "Use either `--PROMPT` or `--prompt-file`, not both."}, exit_code=2)
    if not args.PROMPT and args.prompt_file is None:
        emit_json({"success": False, "error": "Provide `--PROMPT` or `--prompt-file`."}, exit_code=2)
    stdin_file: Optional[Path] = None
    prompt_arg: Optional[str] = args.PROMPT
    if args.prompt_file is not None:
        if not args.prompt_file.is_file():
            emit_json({"success": False, "error": f"Prompt file not found: {args.prompt_file}"}, exit_code=2)
        prompt_arg = None
        stdin_file = args.prompt_file

    cd: Path = args.cd
    error = preflight_check(cd)
    if error:
        emit_json({"success": False, "error": error}, exit_code=1)

    warnings: List[str] = []
    if args.bare and not os.environ.get("ANTHROPIC_API_KEY"):
        warnings.append(
            "--bare ignores OAuth/keychain auth; set ANTHROPIC_API_KEY (or apiKeyHelper via --settings) or the call will fail to authenticate."
        )

    cmd = build_command(args, prompt_arg)

    all_messages: List[Dict[str, Any]] = []
    state: Dict[str, Any] = {
        "agent_messages": "",
        "result_text": None,
        "session_id": None,
        "subtype": None,
        "is_error": False,
        "total_cost_usd": None,
        "usage": {},
        "num_turns": None,
        "tools_used": 0,
        "tools_failed": 0,
        "tool_counts": {},
        "permission_denials": [],
        "terminal_reason": None,
        "stop_reason": None,
        "duration_ms": None,
        "structured_output": None,
        "rate_limited": False,
        "model": None,
        "errors": [],
    }
    raw_json_lines: List[str] = []
    start_time = time.time()
    returncode = 1

    try:
        generator = stream_command(cmd, cwd=cd.absolute(), timeout_seconds=args.timeout, stdin_file=stdin_file)
        while True:
            try:
                line = next(generator)
            except StopIteration as finished:
                returncode = int(finished.value or 0)
                break

            if args.output_format == "stream-json":
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    state["errors"].append(f"[json decode error] {line}")
                    continue
                if isinstance(event, dict):
                    summarize_event(event, all_messages, state, start_time)
            elif args.output_format == "json":
                raw_json_lines.append(line)
            else:  # text
                state["agent_messages"] += line + "\n"
    except Exception as exc:  # pragma: no cover - defensive boundary
        emit_json({"success": False, "error": f"Failed to run Claude Code: {exc}", "warnings": warnings}, exit_code=1)

    if args.output_format == "json":
        parse_json_blob(raw_json_lines, all_messages, state)
    elif args.output_format == "text":
        state["agent_messages"] = state["agent_messages"].strip()

    agent_messages = state["agent_messages"] or state["result_text"] or ""

    # Determine success: prefer the authoritative result-event subtype; fall back to exit code.
    if state["subtype"] is not None:
        success = state["subtype"] == "success" and not state["is_error"]
    else:
        success = returncode == 0

    session_expected = args.output_format in ("json", "stream-json") and not args.no_session_persistence
    if success and state["session_id"] is None and session_expected:
        warnings.append("Could not capture SESSION_ID; multi-turn resume will not be possible for this run.")

    if not success:
        if state["subtype"] and state["subtype"] != "success":
            state["errors"].append(f"Claude terminated with subtype: {state['subtype']}.")
        if returncode != 0:
            state["errors"].append(f"Claude Code exited with non-zero status: {returncode}.")
        if args.timeout and returncode != 0:
            state["errors"].append(f"Claude may have timed out after {args.timeout:g} seconds.")
        if not agent_messages and not state["errors"]:
            state["errors"].append("No response captured from Claude Code.")

    result: Dict[str, Any] = {"success": success}
    if state["session_id"] is not None:
        result["SESSION_ID"] = state["session_id"]
    result["agent_messages"] = agent_messages
    if state["model"]:
        result["model"] = state["model"]
    if state["subtype"]:
        result["subtype"] = state["subtype"]
    if state["is_error"]:
        result["is_error"] = True
    if state["total_cost_usd"] is not None:
        result["total_cost_usd"] = state["total_cost_usd"]
    if state["usage"]:
        usage = state["usage"]
        compact = {
            key: usage.get(key)
            for key in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            if usage.get(key) is not None
        }
        if compact:
            result["usage"] = compact
    if state["num_turns"] is not None:
        result["num_turns"] = state["num_turns"]
    if state["tools_used"]:
        result["tools_used"] = state["tools_used"]
    if state["tools_failed"]:
        result["tools_failed"] = state["tools_failed"]
    if state["tool_counts"]:
        result["tool_counts"] = state["tool_counts"]
    if state["permission_denials"]:
        result["permission_denials"] = state["permission_denials"]
    if state["structured_output"] is not None:
        result["structured_output"] = state["structured_output"]
    if state["rate_limited"]:
        result["rate_limited"] = True
    if warnings:
        result["warnings"] = warnings
    if not success:
        result["error"] = "\n".join(str(err) for err in state["errors"] if err) or "No response from Claude Code."
    if args.return_all_messages:
        result["all_messages"] = all_messages

    print(json.dumps(result, indent=2, ensure_ascii=False))
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
