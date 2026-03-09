# Grok Deep Search

Standalone Codex skill for Grok-backed web search and deep research.

## Layout

- `SKILL.md` - trigger and usage guide
- `agents/openai.yaml` - UI metadata
- `scripts/grok_search.py` - self-contained CLI helper (zero external dependencies)
- `references/prompt-contract.md` - prompt contract for search modes

## Configuration

The script reads configuration from a local `.env` file in the repo root.

## `.env` Setup

Copy the example file and fill in your values:

```powershell
Copy-Item .\.env.example .\.env
```

Then edit `.env`:

```dotenv
GROK_API_KEY=sk-your-key-here
# Optional:
GROK_BASE_URL=http://localhost:3005/v1
GROK_MODEL=grok-4.20-beta
```

### Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROK_API_KEY` | ✅ Yes | *(none)* | Your NewAPI / Grok gateway API key |
| `GROK_BASE_URL` | No | `http://localhost:3005/v1` | Base URL of the OpenAI-compatible endpoint |
| `GROK_MODEL` | No | `grok-4.20-beta` | Model name to use |

## Recommended Gateway

If you need a local/self-hosted upstream, `grok2api` is a good fit for this skill:

- `https://github.com/chenyme/grok2api`

This skill expects an OpenAI-compatible `chat/completions` endpoint, so `grok2api` or a compatible NewAPI gateway works well.

## Install Into Global Skills

Copy the folder:

```powershell
robocopy . "$env:USERPROFILE\.codex\skills\grok-deep-search" /E
```

Or create a junction during local iteration:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.codex\skills\grok-deep-search" -Target "E:\Project\grok-deep-search"
```

## Usage

```powershell
py -3 .\scripts\grok_search.py search --query "查一下 browser agent 方向最近有哪些开源实现" --depth deep
py -3 .\scripts\grok_search.py continue --report ".\research\2026-03-09-browser-agent\report.md" --query "继续比较最活跃的三个仓库"
```

Reports are saved under the current working directory in `research/`.
