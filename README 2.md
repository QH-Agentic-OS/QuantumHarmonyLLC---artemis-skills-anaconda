# Anaconda Agent Studio (plugin)

Packages the **anaconda-agent-studio** skill as an installable plugin.

## What it does

Gives Claude expert knowledge for building on **Anaconda Agent Studio**, the Beta desktop app for local AI agents. Once installed, Claude will automatically use it when you:

- Scaffold a new Agent Studio agent project from scratch
- Author the moving parts — `agent.yaml`, `pixi.toml`, Python `@tool` modules, `mcp.json`, and skills
- Register an existing MCP server, Claude skill, or ATP agent into the Agent Studio catalog
- Wire multi-agent setups where agents call each other over MCP

## Triggers

Claude loads the skill when you mention Anaconda Agent Studio, `agent.yaml`, `pixi.toml`, `anaconda_agent_runtime`, `@tool` decorators with that runtime, tool servers, or ask to "build an agent in Anaconda" or "make my Claude skill work in Anaconda."

## Contents

- `skills/anaconda-agent-studio/` — the full skill: `SKILL.md`, reference guides (project structure, `agent.yaml` spec, build & run, tool authoring, orchestration, ATP bridge, skills-in-Anaconda, troubleshooting), asset templates, and an agent-validation script.

## Install

Open the `.plugin` file in Cowork and press install, or add it through Settings → Capabilities.

## License

Apache-2.0 (see `skills/anaconda-agent-studio/LICENSE`).
