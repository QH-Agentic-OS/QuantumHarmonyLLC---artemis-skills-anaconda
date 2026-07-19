# Build & run — the end-to-end command walkthrough

`project_structure.md` covers *what file goes where*. This covers *how to actually
build the thing and prove it runs* — the commands, the order, and the
"did it work?" checks at each step. Read this when the user says "build me an
agent," "it won't load," or "how do I run this."

Two facts shape everything below:

1. **Agent Studio is the run surface.** You load a project folder into the
   desktop app and run it there; there is no fully-documented headless "run this
   agent.yaml from a terminal" command in the Beta. So the build job is: get the
   project into a state Agent Studio can ingest without complaint, then load it.
2. **`pixi` is the environment.** The tools' Python environment is a pixi
   workspace. You can — and should — resolve it from the terminal *before*
   loading, because a failed solve is far easier to read in `pixi`'s output than
   in the app's one-line error toast.

So the through-line is: **scaffold the files → resolve the env with pixi →
preflight-validate → load into Agent Studio → smoke-test → verify it loaded.**
Each step has a check you can see pass before moving on.

---

## 0. Prerequisites (surface these before building, not after)

- **Anaconda Desktop** installed, with **BETA Features → Agent Studio** toggled on
  in Settings, and Agent Studio downloaded (it installs on first open, after you
  accept its Privacy Policy / ToS).
- **Docker Desktop** installed *and running* — required whenever `sandbox.enabled`
  is true (the default). If the user isn't sandboxing, say so explicitly.
- **`pixi`** on PATH. Quick check: `pixi --version`. If missing:
  `curl -fsSL https://pixi.sh/install.sh | bash` (macOS/Linux) then restart the
  shell, or install from conda-forge.
- **The runtime wheel** (`anaconda_agent_runtime-*.whl`) if you're building
  offline — it goes in `packages/`. Online, you can depend on it from PyPI
  instead (see step 2).
- An **AI provider** configured in Agent Studio (**Manage → AI Provider**). The
  hosted `anaconda` provider needs no setup; `anaconda-desktop` needs a local
  model server running; others need an API key.

If any of these is missing, fix it first — most "Agent Studio is broken" reports
are actually one of these five not being in place.

---

## 1. Scaffold the files

Create the directory and the skeleton. Copy the templates from `assets/` rather
than writing from memory — they carry the correct field names and comments.

```bash
mkdir -p my-agent/{tools,skills,documents,packages}
cd my-agent
cp /path/to/skill/assets/agent_yaml_template.yaml  agent.yaml
cp /path/to/skill/assets/pixi_toml_template.toml   pixi.toml
cp /path/to/skill/assets/mcp_json_template.json    tools/mcp.json   # only if using MCP
cp /path/to/skill/assets/tool_module_template.py   tools/main.py
: > tools/__init__.py    # empty, makes tools/ a package
```

Then fill in `agent.yaml` (name, description, provider/model, system prompt,
capability list) and write your real `@tool` functions in `tools/main.py`. See
`agent_yaml_spec.md` and `tool_authoring.md`. Delete `tools/mcp.json` if the
agent calls no external MCP servers — an empty/example-only file is just noise.

**Check:** `ls -R` shows `agent.yaml`, `pixi.toml`, `tools/__init__.py`, and at
least one `tools/*.py`.

---

## 2. Resolve the environment with pixi

This is the step most "build" guides skip, and it's where the majority of
load-time failures actually originate. Resolving in the terminal turns a cryptic
app error into a readable solver message.

Point the runtime dependency at either a local wheel or PyPI (in `pixi.toml`):

```toml
# Offline — local wheel in packages/:
[pypi-dependencies]
anaconda_agent_runtime = { path = "packages/anaconda_agent_runtime-0.1.0-py3-none-any.whl" }

# OR online — from PyPI:
# [pypi-dependencies]
# anaconda_agent_runtime = ">=0.1.0"
```

Then resolve and verify:

```bash
pixi install                                   # solves deps, writes pixi.lock
pixi list | grep -i anaconda_agent_runtime     # runtime is actually installed
pixi run python -c "import anaconda_agent_runtime; print('runtime OK')"
```

Add any package a tool imports through pixi (this is what Agent Studio's
**Dependencies** dialog does under the hood — fine to do by hand while
bootstrapping):

```bash
pixi add pandas requests          # conda packages, preferred
pixi add --pypi some-pypi-only-pkg
```

**Check:** `pixi install` exits 0, `pixi.lock` exists, and the `import` line
prints `runtime OK`. If it doesn't, you've found the problem here instead of
inside the app — see `troubleshooting.md` → "conda / pixi build layer."

---

## 3. Preflight-validate

Before loading, run the bundled validator. It parses `agent.yaml`, `pixi.toml`,
and `tools/mcp.json` against the documented schema and catches the things Agent
Studio reports as a single opaque failure — a bad provider name, a `localhost`
URL that won't resolve from the sandbox, a tool path that doesn't exist, a
`tools/mcp.json#key` reference with no matching server.

```bash
python /path/to/skill/scripts/validate_agent.py .
# add --strict to treat warnings as failures (good for a CI gate)
```

**Check:** `RESULT: PASS`. Fix every ERROR before continuing — each one is a
load failure you'd otherwise hit blind.

---

## 4. Load into Agent Studio

Open Agent Studio → **Agents** → **Open** (or drag the project folder onto the
Agents page). Agent Studio reads `agent.yaml` and renders the config page:
provider, system prompt, and the **Capabilities** list (Python tools, MCP
servers, skills, plugins).

**Check (verify it loaded — don't skip this):**

- Every `@tool` function appears in the tools list. *Missing tools* → the module
  didn't import; check `tools/__init__.py` exists and the dependency the tool
  imports is in `pixi.toml` (step 2).
- The provider/model resolves (no red "provider not found"). *If red* → the
  `provider`/`model` in `agent.yaml` doesn't match a configured AI Provider
  exactly; for `anaconda-desktop`, the local model server must be running.
- Listed skills show up under Capabilities. *Missing* → the `skills/<name>/`
  folder is missing its `SKILL.md`.
- If sandboxed: the sandbox indicator is healthy (Docker is running).

---

## 5. Smoke-test in chat

Open the agent and send one message that *forces a tool call* — not "hi", but
something only a tool can answer (e.g. "how many rows are in
`/work/input/sales.csv`?"). Watch that:

- the agent calls the tool (it appears in the run/Agent Monitor timeline),
- approval prompts fire for anything you set to `ask`,
- the result comes back from the tool, not a hallucinated guess.

**Check:** the tool actually ran. If the agent *describes* what it would do
instead of doing it, the docstring is too weak or the tool's approval is
`disabled` — see `tool_authoring.md` → docstring craft, and `troubleshooting.md`
→ "tool calls silently not happening."

---

## 6. Iterate

The edit loop is tight: change a `tools/*.py` or `agent.yaml`, re-run the
validator, reload the agent in Agent Studio (re-open the project), re-test the
one prompt. Keep `pixi.lock` under version control so the environment is
reproducible for whoever you hand the project to.

---

## Variant: Tool Server (an agent with no model)

A Tool Server is the same `tools/` build with no `agent.yaml` model/prompt — pure
MCP server exposing Python tools, for sharing across agents or with external
clients (Claude Desktop, Cursor, VS Code). Build `tools/` exactly as above,
resolve with pixi, create it via **Create → Tool Server**, start it, and copy its
**SSE URL** from the Connect dialog. Register that URL wherever you need the
tools. See `orchestration.md`.

## Variant: multi-agent (agent A calls agent B)

Every running agent is already an MCP server on localhost. Start agent B, copy
its **MCP server (SSE)** URL from **Connect**, register it (Add-ons → MCP → Add →
SSE, or in A's `tools/mcp.json`), and enable it in A's Capabilities. From inside
A's sandbox the URL must be `http://host.docker.internal:<port>/sse`, never
`localhost`. Full pattern in `orchestration.md`.

---

## The whole loop, condensed

```bash
mkdir -p my-agent/{tools,skills,documents,packages} && cd my-agent
# ...copy templates, fill agent.yaml, write tools/*.py...
pixi install && pixi run python -c "import anaconda_agent_runtime; print('OK')"
python /path/to/skill/scripts/validate_agent.py . --strict
# Agent Studio → Agents → Open → drag folder → verify tools+provider → smoke-test
```

If a step's check fails, stop there — the failure is local to that step, and
`troubleshooting.md` is organized by exactly these layers.
