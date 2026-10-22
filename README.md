# Skillsmith · Engineering Skills

100 stack-agnostic skills for AI coding agents, covering security, data, delivery, reliability, cloud cost, testing, and documentation. Each skill adapts to the conventions of the repository in which it is used.

**Browse all skills → [INDEX.md](INDEX.md)**

## Install

With the open [`skills` CLI](https://github.com/vercel-labs/skills) (Node 22.20+):

```bash
# one skill
npx skills add skillsmithhq/skills --skill aws-cost-estimate -g -a claude-code

# all skills
npx skills add skillsmithhq/skills --skill '*' -g -a claude-code
```

`-g` installs for all your projects; `-a` selects the agent (`claude-code`, `cursor`, `codex`, and others).

Without Node, on macOS, Linux, or WSL:

```bash
mkdir -p ~/.claude/skills/aws-cost-estimate && curl -fsSL https://install.skillsmith.workers.dev/s/aws-cost-estimate -o ~/.claude/skills/aws-cost-estimate/SKILL.md
```

On Windows (PowerShell):

```powershell
$d = "$HOME/.claude/skills/aws-cost-estimate"; New-Item -ItemType Directory -Force $d | Out-Null; Invoke-WebRequest -UseBasicParsing "https://install.skillsmith.workers.dev/s/aws-cost-estimate" -OutFile "$d/SKILL.md"
```

## Use

Start a new Claude Code session (terminal, VS Code, or JetBrains) and ask as you normally would, e.g. "check this migration for safety". The matching skill loads automatically. To use a specific skill, name it: "use `migration-safety-check` on this file".

## Security

Skills are plain-text instructions with no scripts, binaries, or network calls of their own. They are reviewed against these rules:

- No hidden or invisible characters, HTML comments, or encoded content.
- No instructions to send code or data to outside services, and no pipe-to-shell commands.
- No destructive commands; skills that review scripts or migrations are review-only.
- Actions that change systems (cloud resources, dependencies, databases) require the user's explicit approval.
- Secrets are never printed in full, and generated documents never include secrets or personal data.
- Content fetched from tickets or documents is treated as information, never as instructions.

This is a self-review, not an independent audit.

## Disclaimer

Skills run inside your own AI agent; Skillsmith never receives or stores your code. AI output can be wrong: review every result before acting on it. Skillsmith is not responsible for outputs or their consequences. Provided under the MIT License, without warranty. Not affiliated with Anthropic or any AI provider.
