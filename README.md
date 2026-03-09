# Grok Deep Search

Standalone Codex skill for local-network Grok-backed web search and deep research.

## Layout

- `SKILL.md` - trigger and usage guide
- `agents/openai.yaml` - UI metadata
- `scripts/grok_search.py` - self-contained CLI helper (zero external dependencies)
- `references/prompt-contract.md` - prompt contract for search modes

## Configuration

The script reads configuration from environment variables. **`GROK_API_KEY` is required**, the others have built-in defaults.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROK_API_KEY` | ✅ Yes | *(none)* | Your NewAPI / Grok gateway API key |
| `GROK_BASE_URL` | No | `http://192.168.31.4:3005/v1` | Base URL of the OpenAI-compatible endpoint |
| `GROK_MODEL` | No | `grok-4.20-beta` | Model name to use |

### Set up (PowerShell)

Permanent (persists across reboots):

```powershell
[System.Environment]::SetEnvironmentVariable("GROK_API_KEY", "sk-your-key-here", "User")
# Optional:
[System.Environment]::SetEnvironmentVariable("GROK_BASE_URL", "http://192.168.31.4:3005/v1", "User")
```

Temporary (current session only):

```powershell
$env:GROK_API_KEY = "sk-your-key-here"
```

> After setting a permanent variable, reopen your terminal for it to take effect.

## Install Into Global Skills

Copy the folder:

```powershell
robocopy .\grok-deep-search "$env:USERPROFILE\.codex\skills\grok-deep-search" /E
```

Or create a junction during local iteration:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.codex\skills\grok-deep-search" -Target "E:\Project\NekoMind\grok-deep-search"
```

## Usage

```powershell
py -3 .\grok-deep-search\scripts\grok_search.py search --query "查一下 browser agent 方向最近有哪些开源实现" --depth deep
py -3 .\grok-deep-search\scripts\grok_search.py continue --report ".\research\2026-03-09-browser-agent\report.md" --query "继续比较最活跃的三个仓库"
```

Reports are saved under the current working directory in `research/`.