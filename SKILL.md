---
name: grok-deep-search
description: Delegate network search and deep research to a local Grok-backed NewAPI service. Use when Codex needs current web information, wants to check for existing implementations, papers, or community writeups before starting a project, or should continue a saved Grok research thread.
---

# Grok Deep Search

Use this skill to offload web search and deeper research passes to the local Grok gateway at `http://192.168.31.4:3005/v1`.

Run the helper through `scripts/grok_search.py`.

## When To Use

Prefer this skill when any of these are true:
- The user wants network search, current information, useful links, or a quick web-backed answer.
- The user is about to start a project and wants to check whether papers, products, open-source repos, or community implementations already exist.
- The task needs a deeper report with tradeoffs, risks, and practical next steps.
- The user wants to continue a previous Grok research thread from a saved `report.md`.

Use `normal` depth for lightweight web lookups and `deep` for broader pre-project research. Both depths use the same Grok model; the difference is the prompt and the expected report depth.

## Quick Start

```powershell
py -3 path\to\grok_search.py search --query "查一下这个库最近还在维护吗" --depth normal
py -3 path\to\grok_search.py search --query "开工前先查一下这个方向有没有论文和开源实现" --depth deep --topic "agent-browser-research"
py -3 path\to\grok_search.py continue --report ".\research\2026-03-09-agent-browser-research\report.md" --query "继续对比最强的三个开源实现"
```

When the report should live under a project, run the helper from that project directory so the output lands in `./research/` there.

## Search Workflow

Follow this sequence:
1. Choose a depth.
   - `normal`: latest status checks, maintenance checks, quick comparisons, link gathering.
   - `deep`: project scouting, prior-art review, paper and repo discovery, broader synthesis.
2. Run `search` with the user query.
3. Read the generated `report.md`, then summarize the key findings back in chat.
4. If the user wants follow-up digging, run `continue` against the saved report.

`search` creates `research/YYYY-MM-DD-slug/` in the current working directory and writes:
- `report.md` - the main natural-language report
- `conversation.md` - the prompt/response trail used for later continuation

## Continue Research

Use `continue` when the user says things like:
- “继续挖”
- “补充这个方向”
- “基于上次结果再比较一下”
- “沿着这条线继续搜”

Pass the saved `report.md`. The helper loads the existing report plus the latest `conversation.md` context if present, asks Grok to continue the same thread, and appends the new round to both files.

## Output Expectations

- `normal` returns a concise natural-language report with the answer, key findings, and useful links.
- `deep` returns a broader report that should cover prior art, representative papers/projects/repos, tradeoffs, risks, and a practical recommendation.
- Match the user's language. If the query is in Chinese, answer in Chinese unless the user asks otherwise.
- For time-sensitive claims, prefer concrete dates and direct URLs.
- Mention that the findings come from Grok-backed web research when that context matters.

## Files

- `scripts/grok_search.py` - helper CLI that talks to the local Grok-backed NewAPI endpoint
- `references/prompt-contract.md` - prompt and output rules for `normal`, `deep`, and `continue`
- `README.md` - installation and portability notes for copying this skill into another agent environment

If the local gateway, key, or model changes later, update the constants near the top of `scripts/grok_search.py`.