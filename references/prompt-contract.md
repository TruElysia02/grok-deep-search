# Prompt Contract

This file defines the working contract for `scripts/grok_search.py`.

## `search --depth normal`

Use for lightweight network search:
- latest status checks
- maintenance checks
- quick comparisons
- link gathering

Prompt goals:
- use Grok web research/search abilities
- answer concisely
- include direct URLs
- mention concrete dates for time-sensitive claims
- mirror the user's language

## `search --depth deep`

Use for broader prior-art research:
- papers
- open-source repos
- products or existing implementations
- community writeups
- tradeoffs and recommendations

Prompt goals:
- perform a broader research pass
- synthesize rather than dump raw links
- keep the report natural-language Markdown
- include practical recommendations and next steps
- mirror the user's language

## `continue`

Inputs:
- follow-up query
- saved `report.md`
- tail of `conversation.md` when available

Prompt goals:
- continue the same topic instead of restarting from scratch
- reuse prior findings where relevant
- search the web again when needed
- avoid repeating unchanged background
- append a usable follow-up report section

## Output Expectations

- Natural-language Markdown, not rigid JSON
- Useful links over filler
- Clear uncertainty when evidence is thin
- Concrete dates when recency matters