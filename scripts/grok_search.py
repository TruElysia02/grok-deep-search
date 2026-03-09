#!/usr/bin/env python3
from __future__ import annotations

import os

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib import error, request


BASE_URL = os.environ.get("GROK_BASE_URL", "http://192.168.31.4:3005/v1")
API_KEY = os.environ.get("GROK_API_KEY", "")
MODEL = os.environ.get("GROK_MODEL", "grok-4.20-beta")
TIMEOUT_SEC = 180
DEFAULT_DEPTH = "deep"
REPORT_FILE = "report.md"
CONVERSATION_FILE = "conversation.md"


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class GrokSearchError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grok-backed network search and deep research helper."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser(
        "search", help="Start a new Grok-backed search or research thread."
    )
    search_parser.add_argument("--query", required=True, help="Search query or research request.")
    search_parser.add_argument(
        "--depth",
        choices=("normal", "deep"),
        default=DEFAULT_DEPTH,
        help="Report depth. 'normal' is concise, 'deep' is broader and more analytical.",
    )
    search_parser.add_argument(
        "--topic",
        help="Optional short label for the output folder. Defaults to a slug from the query.",
    )

    continue_parser = subparsers.add_parser(
        "continue", help="Continue a previous research thread from a saved report."
    )
    continue_parser.add_argument("--report", required=True, help="Path to an existing report.md file.")
    continue_parser.add_argument("--query", required=True, help="Follow-up question for the same topic.")

    return parser.parse_args()


def slugify(value: str, *, limit: int = 48) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        return "research"
    return slug[:limit].rstrip("-") or "research"


def unique_directory(base_dir: Path) -> Path:
    if not base_dir.exists():
        return base_dir
    suffix = 2
    while True:
        candidate = base_dir.with_name(f"{base_dir.name}-{suffix}")
        if not candidate.exists():
            return candidate
        suffix += 1


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(content)


def tail_text(content: str, *, limit: int = 12000) -> str:
    if len(content) <= limit:
        return content
    return content[-limit:]


def call_chat(messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
    if not API_KEY:
        raise GrokSearchError(
            "GROK_API_KEY environment variable is not set. "
            "Set it before running: set GROK_API_KEY=sk-your-key"
        )
    payload = {
        "model": MODEL,
        "messages": [{"role": item.role, "content": item.content} for item in messages],
        "temperature": temperature,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{BASE_URL.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=TIMEOUT_SEC) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GrokSearchError(f"HTTP {exc.code} from NewAPI: {detail}") from exc
    except error.URLError as exc:
        raise GrokSearchError(f"Failed to reach NewAPI at {BASE_URL}: {exc.reason}") from exc

    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GrokSearchError(f"Unexpected response payload: {raw[:400]}") from exc

    if not isinstance(content, str) or not content.strip():
        raise GrokSearchError("NewAPI returned an empty message content.")

    finish_reason = data["choices"][0].get("finish_reason", "")
    if finish_reason == "length":
        print("[WARN] Response was truncated by the server (finish_reason=length).", file=sys.stderr)

    return content.strip()


def build_search_messages(query: str, depth: str) -> list[ChatMessage]:
    today = datetime.now().strftime("%Y-%m-%d")
    style_hint = "Keep the answer concise." if depth == "normal" else "Go broader and synthesize what matters."
    scope_hint = (
        "Focus on a quick network-backed answer, useful links, and concrete dates when recency matters."
        if depth == "normal"
        else "Focus on prior art, representative papers/projects/repos, tradeoffs, and concrete recommendations."
    )
    system_prompt = (
        "You are a Grok-backed research assistant using your own web search and browsing abilities. "
        "Verify claims with web evidence when needed, prefer direct URLs, and match the user's language. "
        "If the query is in Chinese, answer in Chinese unless asked otherwise."
    )
    user_prompt = (
        f"Today is {today}.\n"
        f"Research depth: {depth}.\n"
        f"Task: {query}\n\n"
        f"{scope_hint}\n"
        f"{style_hint}\n"
        "Return natural-language Markdown, not JSON. Use headings when helpful. "
        "State uncertainty clearly if evidence is weak."
    )
    return [ChatMessage("system", system_prompt), ChatMessage("user", user_prompt)]


def build_continue_messages(query: str, prior_report: str, prior_conversation: str) -> list[ChatMessage]:
    today = datetime.now().strftime("%Y-%m-%d")
    system_prompt = (
        "You are continuing an existing Grok-backed web research thread. "
        "Use your web search and browsing abilities when needed, build on prior findings instead of restarting, "
        "and match the user's language."
    )
    user_prompt = (
        f"Today is {today}.\n"
        "We are continuing an existing research thread.\n\n"
        f"Previous report:\n{tail_text(prior_report, limit=18000)}\n\n"
        f"Recent conversation trail:\n{tail_text(prior_conversation, limit=12000)}\n\n"
        f"Follow-up request: {query}\n\n"
        "Continue the same topic. Avoid repeating unchanged background unless it is needed for clarity. "
        "Return a natural-language Markdown follow-up with useful links, dates for time-sensitive claims, "
        "and an updated recommendation if the new evidence changes the conclusion."
    )
    return [ChatMessage("system", system_prompt), ChatMessage("user", user_prompt)]


def create_report_directory(topic: str) -> Path:
    root = Path.cwd() / "research"
    root.mkdir(parents=True, exist_ok=True)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    candidate = root / f"{date_prefix}-{slugify(topic)}"
    report_dir = unique_directory(candidate)
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def render_report_header(*, title: str, query: str, depth: str) -> str:
    return (
        f"# {title}\n\n"
        f"- Created: {timestamp_now()}\n"
        f"- Depth: {depth}\n"
        f"- Model: {MODEL}\n"
        f"- Query: {query}\n\n"
        "---\n\n"
    )


def render_conversation_round(*, query: str, response: str, label: str) -> str:
    return (
        f"## {label} ({timestamp_now()})\n\n"
        f"### Query\n\n{query}\n\n"
        f"### Response\n\n{response}\n\n"
    )


def run_search(query: str, depth: str, topic: str | None) -> int:
    report_dir = create_report_directory(topic or query)
    report_path = report_dir / REPORT_FILE
    conversation_path = report_dir / CONVERSATION_FILE
    response = call_chat(build_search_messages(query, depth))

    title = topic or query.strip() or "Grok Research"
    write_text(report_path, render_report_header(title=title, query=query, depth=depth) + response + "\n")
    write_text(
        conversation_path,
        "# Conversation\n\n" + render_conversation_round(query=query, response=response, label="Initial Search"),
    )

    print(f"Saved report: {report_path}")
    print(f"Saved conversation: {conversation_path}")
    print()
    print(response)
    return 0


def run_continue(report_arg: str, query: str) -> int:
    report_path = Path(report_arg).expanduser().resolve()
    if not report_path.exists():
        raise GrokSearchError(f"Report not found: {report_path}")
    if report_path.name != REPORT_FILE:
        raise GrokSearchError(f"Expected a {REPORT_FILE} path, got: {report_path}")

    report_dir = report_path.parent
    conversation_path = report_dir / CONVERSATION_FILE
    prior_report = read_text(report_path)
    prior_conversation = read_text(conversation_path) if conversation_path.exists() else ""
    response = call_chat(build_continue_messages(query, prior_report, prior_conversation))

    append_text(
        report_path,
        (
            "\n\n---\n\n"
            f"## Follow-up ({timestamp_now()})\n\n"
            f"**Query:** {query}\n\n"
            f"{response}\n"
        ),
    )
    if conversation_path.exists():
        append_text(conversation_path, render_conversation_round(query=query, response=response, label="Follow-up"))
    else:
        write_text(
            conversation_path,
            "# Conversation\n\n" + render_conversation_round(query=query, response=response, label="Follow-up"),
        )

    print(f"Updated report: {report_path}")
    print(f"Updated conversation: {conversation_path}")
    print()
    print(response)
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "search":
            return run_search(args.query, args.depth, args.topic)
        if args.command == "continue":
            return run_continue(args.report, args.query)
        raise GrokSearchError(f"Unsupported command: {args.command}")
    except GrokSearchError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())