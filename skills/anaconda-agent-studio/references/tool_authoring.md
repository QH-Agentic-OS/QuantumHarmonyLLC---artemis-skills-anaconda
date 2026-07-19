# Tool authoring — `@tool`, modules, and `mcp.json`

Python tools are where the agent's actual *doing* happens. Get this layer right and the rest of the agent falls into place. Get it wrong — bad docstrings, fuzzy type hints, tools that swallow errors — and the agent will hallucinate or stall in ways that are painful to debug.

## How Agent Studio reads a tool

Inside any `.py` file under `tools/`, every function decorated with `@tool` becomes available to the agent. Three things from your code become part of the agent's view of that tool:

1. **Function name** → the tool's name. The agent uses this when deciding which tool to call.
2. **Argument names + type hints** → the tool's input schema. Anaconda generates a JSON schema from these.
3. **Docstring** → the tool's description. This is what the model reads to decide *whether* to call it.

That's it. There's no separate manifest, no decorator-arg overrides for the schema. The function signature is the contract.

## The minimal tool

```python
"""csv_io tool module."""

from anaconda_agent_runtime.tools import tool


@tool
def count_rows(path: str) -> int:
    """Count the rows in a CSV file, excluding the header.

    Args:
        path: Absolute path to the CSV file inside the agent sandbox
              (e.g. /work/input/sales.csv).

    Returns:
        Integer row count. Header row is not counted.
    """
    with open(path) as f:
        return sum(1 for _ in f) - 1
```

This is the whole pattern. The agent now sees a tool called `count_rows` with one required string argument `path`, described by everything in the docstring. The model picks this tool when the user says "how many rows in sales.csv?" — and the docstring is what makes that decision crisp.

## Docstring craft (the part everyone underweights)

The docstring is read by the model on every turn it's deciding which tool to call. It deserves the same care as a tool description in an MCP server. Three rules:

1. **Lead with the verb in present tense.** "Count the rows..." not "This function counts...". Models pattern-match openings.
2. **Make the `Args:` section answer "what exactly do I pass?"** Include format constraints (absolute vs relative path, allowed values, units) right in the description.
3. **Make the `Returns:` section answer "what do I do with the result?"** Mention type, range, and any edge values (e.g., "Returns 0 for empty files, -1 if the file does not exist").

Anti-pattern: docstrings that describe *implementation* ("uses pandas to read the CSV..."). The model doesn't care how. Describe behavior.

## Module organization

Each `.py` file is a logical grouping. Don't put everything in one file; split by domain:

- `tools/csv_io.py` — read, write, validate CSVs
- `tools/sql.py` — query a local database
- `tools/git.py` — git status, diff, log queries

The cost of splitting is near-zero; the benefit is that the agent can be configured to enable some modules and not others, and human readers can find things.

## Type hints — what works, what doesn't

Anaconda generates the input schema from type hints. Works well:

```python
def example(
    name: str,
    count: int = 10,
    enabled: bool = True,
    tags: list[str] = [],
    options: dict[str, str] = {},
) -> str:
```

Works less well: complex `TypedDict`, `Union[X, Y]` with non-primitive types, `Optional[ComplexObject]`. When the type gets exotic, the schema sometimes degrades to "untyped object." If you find yourself wanting that, prefer flattening into multiple primitive args.

`Pydantic` models can be used for richer schemas in the same way FastAPI / FastMCP servers use them, but for most agent tools plain type hints are enough — keep complexity down.

## Tool approval — when to default what

Every tool has an approval state in the UI: `allow`, `ask`, `disabled`. You can't set this in code, but you can recommend it via tool naming and docstring:

- Read-only / idempotent tools (`count_*`, `read_*`, `list_*`, `search_*`) → recommend `allow`.
- Destructive tools (`delete_*`, `send_*`, `publish_*`, `commit_*`, `create_*`) → recommend `ask`.
- Anything the user has never seen the agent do → `ask` until trust is earned.

Mention this in the system prompt too: "Tools prefixed with `delete_` will prompt the user; explain why you want to call them before doing so."

## Dependencies

When a tool needs an external package (`requests`, `pandas`, etc.), add it through the UI: Python Tools editor → Dependencies button (lower-left) → Add dependencies. This updates `pixi.toml`.

Don't hand-edit `pixi.toml` to add deps unless you must — the UI manages the package source resolution, which is easy to get wrong manually.

## `mcp.json` — project-local MCP servers

`tools/mcp.json` defines MCP servers this agent talks to, *scoped to this project*. Format mirrors the standard MCP client config:

```json
{
  "mcpServers": {
    "local_postgres": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-postgres", "--connection-string", "postgresql://localhost/mydb"],
      "env": {}
    },
    "remote_api": {
      "type": "sse",
      "url": "http://host.docker.internal:7000/sse"
    }
  }
}
```

Key fields:

- `type`: `stdio` (the server is a process Agent Studio launches) or `sse` (the server is already running at a URL).
- For `stdio`: `command`, `args`, optional `env`, optional `cwd`.
- For `sse`: just `url`.

Reference this server from `agent.yaml` with `ref: tools/mcp.json#local_postgres`.

### Project-local vs. catalog — when to use each

| Situation | Use |
|---|---|
| Only this agent needs this server | `tools/mcp.json` (project-local) |
| Multiple agents on this machine will use the same server | Add-ons → MCP (global catalog) |
| The server is part of a shipped agent template | `tools/mcp.json` (travels with the project) |
| The server needs per-user credentials | Add-ons → MCP (so each user configures their own) |

### Docker networking gotcha

If the agent runs in a sandbox (the default) and the MCP server runs on the host machine, do NOT use `localhost` or `127.0.0.1` in the URL. The container can't resolve those to the host. Use:

```
http://host.docker.internal:<port>/sse
```

This is the single most common bug in MCP-from-sandbox setups. Set the URL right the first time.

## Quality checklist before declaring a tool done

- [ ] Function name is a verb in lowercase_with_underscores.
- [ ] Every argument has a type hint.
- [ ] Docstring has `Args:` and `Returns:` sections that answer "what do I pass" and "what do I do with the result."
- [ ] Errors that should reach the user are raised; errors the agent should handle return a sentinel value with documented meaning.
- [ ] The function does ONE logical thing. If it's doing two, split it.
- [ ] If the tool is destructive, the name says so (`delete_*`, `commit_*`) and the docstring's first sentence warns.
- [ ] Tested with the agent in a real chat at least once before shipping.
