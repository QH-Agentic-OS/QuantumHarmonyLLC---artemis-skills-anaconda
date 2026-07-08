#!/usr/bin/env python3
"""
validate_agent.py — preflight schema + structure check for an Anaconda Agent
Studio project, BEFORE you hand it to Agent Studio (which tends to fail with
cryptic, one-line errors when something is off).

Run it any time you've hand-edited agent.yaml / pixi.toml / tools/mcp.json, and
always as the last step of scaffolding a new agent.

    python scripts/validate_agent.py /path/to/my-agent
    python scripts/validate_agent.py /path/to/my-agent --strict   # warnings -> failure

Exit code is 0 when there are no ERRORs (1 with --strict if there are WARNs too),
so it drops cleanly into a CI gate or a pre-load check.

It validates against the schema documented in references/agent_yaml_spec.md and
the templates in assets/. It deliberately does NOT import the agent's tools or
start anything — it's a static check, safe to run anywhere.

Dependencies: tomllib (stdlib, py3.11+) for pixi.toml, json (stdlib) for mcp.json.
PyYAML is used for agent.yaml when available; if it isn't, agent.yaml gets a
reduced top-level-key check and a NOTE telling you deep validation was skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---- known-good enums, lifted from agent_yaml_spec.md / templates -----------
PROVIDERS = {"anaconda", "anaconda-desktop", "anthropic", "openai", "google", "groq", "custom"}
NETWORK_MODES = {"outbound", "isolated", "host"}
MOUNT_MODES = {"ro", "rw"}
OUTPUT_FORMATS = {"text", "json"}
APPROVALS = {"allow", "ask", "disabled"}
KNOWN_PLUGINS = {"atlassian", "miro", "nteract", "omni"}  # published as of mid-2026
MCP_TYPES = {"stdio", "sse"}

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

try:
    import yaml  # PyYAML, optional
    HAVE_YAML = True
except ModuleNotFoundError:
    HAVE_YAML = False


class Report:
    """Collects findings and prints a readable, severity-sorted report."""

    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []  # (severity, message)
        self._seen: set[tuple[str, str]] = set()

    def _add(self, sev: str, msg: str) -> None:
        key = (sev, msg)
        if key in self._seen:  # a check may run twice (e.g. mcp.json); report once
            return
        self._seen.add(key)
        self.items.append(key)

    def err(self, msg: str) -> None:
        self._add("ERROR", msg)

    def warn(self, msg: str) -> None:
        self._add("WARN", msg)

    def ok(self, msg: str) -> None:
        self._add("OK", msg)

    def info(self, msg: str) -> None:
        self._add("INFO", msg)

    def note(self, msg: str) -> None:
        self._add("NOTE", msg)

    @property
    def n_err(self) -> int:
        return sum(1 for s, _ in self.items if s == "ERROR")

    @property
    def n_warn(self) -> int:
        return sum(1 for s, _ in self.items if s == "WARN")

    def render(self) -> str:
        glyph = {"ERROR": "✗", "WARN": "▲", "OK": "✓", "INFO": "·", "NOTE": "i"}
        order = {"ERROR": 0, "WARN": 1, "NOTE": 2, "OK": 3, "INFO": 4}
        lines = []
        for sev, msg in sorted(self.items, key=lambda it: order[it[0]]):
            lines.append(f"  {glyph[sev]} [{sev}] {msg}")
        summary = f"\n{self.n_err} error(s), {self.n_warn} warning(s)."
        return "\n".join(lines) + summary


def _load_yaml(path: Path, r: Report):
    text = path.read_text(encoding="utf-8")
    if HAVE_YAML:
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:  # noqa: BLE001
            r.err(f"agent.yaml does not parse as YAML: {e}. "
                  f"Most often a tab character or a misaligned indent — YAML wants spaces.")
            return None
    # Degraded path: no PyYAML. Pull out column-0 top-level keys so we can still
    # check that the load-bearing sections exist.
    r.note("PyYAML not installed — agent.yaml got a reduced check "
           "(top-level keys only). `pip install pyyaml` for full validation.")
    top = set(re.findall(r"^([a-zA-Z_][\w-]*):", text, flags=re.MULTILINE))
    return {"__top_keys_only__": True, "__keys__": top, "__text__": text}


def validate_agent_yaml(proj: Path, r: Report) -> dict | None:
    p = proj / "agent.yaml"
    if not p.exists():
        r.err("agent.yaml is missing. It is the root manifest — Agent Studio "
              "cannot load a project without it.")
        return None
    data = _load_yaml(p, r)
    if data is None:
        return None

    # Degraded (no PyYAML): only check top-level key presence and bail.
    if isinstance(data, dict) and data.get("__top_keys_only__"):
        keys = data["__keys__"]
        for req in ("name", "description"):
            (r.ok if req in keys else r.err)(
                f"agent.yaml top-level key '{req}' "
                + ("present." if req in keys else "missing (required).")
            )
        for opt in ("ai_provider", "sandbox", "knowledge", "capabilities"):
            if opt in keys:
                r.info(f"agent.yaml section '{opt}' present.")
        return data

    if not isinstance(data, dict):
        r.err("agent.yaml parsed but is not a mapping at the top level.")
        return None

    # name / description ------------------------------------------------------
    for req in ("name", "description"):
        v = data.get(req)
        if not isinstance(v, str) or not v.strip():
            r.err(f"agent.yaml: '{req}' is required and must be a non-empty string.")
        elif "<" in v and ">" in v:
            r.warn(f"agent.yaml: '{req}' still contains a <PLACEHOLDER> — fill it in.")
        else:
            r.ok(f"agent.yaml: '{req}' set.")

    # ai_provider -------------------------------------------------------------
    ap = data.get("ai_provider")
    if ap is None:
        r.info("agent.yaml: no ai_provider block — defaults to the hosted "
               "'anaconda' provider (Claude Sonnet 4.6).")
    elif not isinstance(ap, dict):
        r.err("agent.yaml: ai_provider must be a mapping.")
    else:
        prov = ap.get("provider")
        if prov is None:
            r.warn("agent.yaml: ai_provider.provider omitted (will default to 'anaconda').")
        elif prov not in PROVIDERS:
            r.err(f"agent.yaml: ai_provider.provider '{prov}' is not one of {sorted(PROVIDERS)}.")
        else:
            r.ok(f"agent.yaml: provider '{prov}'.")
            if prov == "anaconda-desktop":
                r.info("provider 'anaconda-desktop' needs a model server running "
                       "in Anaconda Desktop at run time, or the agent won't start.")
        if not ap.get("model"):
            r.warn("agent.yaml: ai_provider.model not set — set it to a model the "
                   "chosen provider actually exposes.")
        temp = ap.get("temperature")
        if temp is not None and not (isinstance(temp, (int, float)) and 0.0 <= temp <= 2.0):
            r.err(f"agent.yaml: ai_provider.temperature {temp!r} out of range 0.0–2.0.")
        ofmt = ap.get("output_format")
        if ofmt is not None and ofmt not in OUTPUT_FORMATS:
            r.err(f"agent.yaml: ai_provider.output_format '{ofmt}' must be one of {sorted(OUTPUT_FORMATS)}.")

    # sandbox -----------------------------------------------------------------
    sb = data.get("sandbox")
    sandbox_enabled = True
    if isinstance(sb, dict):
        sandbox_enabled = bool(sb.get("enabled", True))
        net = sb.get("network")
        if net is not None and net not in NETWORK_MODES:
            r.err(f"agent.yaml: sandbox.network '{net}' must be one of {sorted(NETWORK_MODES)}.")
        mounts = sb.get("mounts") or []
        if not isinstance(mounts, list):
            r.err("agent.yaml: sandbox.mounts must be a list.")
        else:
            for i, m in enumerate(mounts):
                if not isinstance(m, dict):
                    r.err(f"agent.yaml: sandbox.mounts[{i}] must be a mapping.")
                    continue
                for k in ("host_path", "sandbox_path"):
                    if not m.get(k):
                        r.err(f"agent.yaml: sandbox.mounts[{i}] missing '{k}'.")
                mode = m.get("mode")
                if mode is not None and mode not in MOUNT_MODES:
                    r.err(f"agent.yaml: sandbox.mounts[{i}].mode '{mode}' must be 'ro' or 'rw'.")
        if sandbox_enabled:
            r.info("sandbox enabled — Docker Desktop must be installed and running, "
                   "and any host service the agent calls must use host.docker.internal, not localhost.")
    elif sb is not None:
        r.err("agent.yaml: sandbox must be a mapping.")

    # knowledge.documents -----------------------------------------------------
    know = data.get("knowledge")
    if isinstance(know, dict):
        for doc in (know.get("documents") or []):
            if isinstance(doc, str) and not (proj / doc).exists():
                r.err(f"agent.yaml: knowledge.documents references '{doc}', which does not exist.")
        sp = know.get("system_prompt")
        if isinstance(sp, str) and "<" in sp and ">" in sp:
            r.warn("agent.yaml: knowledge.system_prompt still contains <PLACEHOLDER> text.")

    # capabilities ------------------------------------------------------------
    caps = data.get("capabilities")
    if isinstance(caps, dict):
        _validate_capabilities(proj, caps, sandbox_enabled, r)
    elif caps is not None:
        r.err("agent.yaml: capabilities must be a mapping.")

    return data


def _validate_capabilities(proj: Path, caps: dict, sandbox_enabled: bool, r: Report) -> None:
    # python_tools
    for t in (caps.get("python_tools") or []):
        if not isinstance(t, str):
            continue
        tp = proj / t
        if not tp.exists():
            r.err(f"capabilities.python_tools references '{t}', which does not exist.")
        else:
            try:
                if "@tool" not in tp.read_text(encoding="utf-8"):
                    r.warn(f"'{t}' has no @tool decorator — Agent Studio will load no "
                           f"tools from it. Decorate at least one function.")
                else:
                    r.ok(f"tool module '{t}' present and has @tool.")
            except OSError:
                pass

    # mcp_servers (and cross-check refs into tools/mcp.json)
    mcp_keys = _mcp_json_keys(proj, r)
    for i, srv in enumerate(caps.get("mcp_servers") or []):
        if not isinstance(srv, dict):
            r.err(f"capabilities.mcp_servers[{i}] must be a mapping.")
            continue
        if not srv.get("name"):
            r.err(f"capabilities.mcp_servers[{i}] missing 'name'.")
        ref = srv.get("ref")
        if ref is None:
            r.err(f"capabilities.mcp_servers[{i}] missing 'ref' (use 'catalog' or 'tools/mcp.json#<key>').")
        elif ref == "catalog":
            r.info(f"mcp server '{srv.get('name')}' references the global catalog "
                   f"(Add-ons → MCP) — make sure it's registered there.")
        elif ref.startswith("tools/mcp.json#"):
            key = ref.split("#", 1)[1]
            if mcp_keys is not None and key not in mcp_keys:
                r.err(f"mcp_servers[{i}].ref points at '{key}' but tools/mcp.json "
                      f"has no such server (found: {sorted(mcp_keys) or 'none'}).")
            else:
                r.ok(f"mcp server '{srv.get('name')}' wired to tools/mcp.json#{key}.")
        else:
            r.warn(f"mcp_servers[{i}].ref '{ref}' is neither 'catalog' nor 'tools/mcp.json#<key>'.")
        for tool, state in (srv.get("approvals") or {}).items():
            if state not in APPROVALS:
                r.err(f"mcp_servers[{i}].approvals['{tool}'] = '{state}' "
                      f"must be one of {sorted(APPROVALS)}.")

    # skills
    for s in (caps.get("skills") or []):
        if not isinstance(s, str):
            continue
        if s.startswith("catalog:"):
            r.info(f"skill '{s}' comes from the Add-ons → Skills catalog.")
            continue
        sp = proj / s / "SKILL.md"
        if not sp.exists():
            r.err(f"capabilities.skills references '{s}' but {s}/SKILL.md does not exist.")
        else:
            r.ok(f"skill '{s}' present.")

    # plugins
    for pl in (caps.get("plugins") or []):
        if pl not in KNOWN_PLUGINS:
            r.warn(f"capabilities.plugins lists '{pl}', not in the known published "
                   f"set {sorted(KNOWN_PLUGINS)} — confirm it exists in your build.")


def _mcp_json_keys(proj: Path, r: Report):
    """Validate tools/mcp.json and return the set of server keys (or None if absent/broken)."""
    p = proj / "tools" / "mcp.json"
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        r.err(f"tools/mcp.json does not parse as JSON: {e}")
        return None
    servers = raw.get("mcpServers")
    if not isinstance(servers, dict):
        r.err("tools/mcp.json has no 'mcpServers' object.")
        return None
    keys = set()
    for name, cfg in servers.items():
        if name.startswith("_"):  # _comment / _example_* are documentation, skip
            continue
        keys.add(name)
        if not isinstance(cfg, dict):
            r.err(f"tools/mcp.json: server '{name}' is not an object.")
            continue
        typ = cfg.get("type")
        if typ not in MCP_TYPES:
            r.err(f"tools/mcp.json: server '{name}' type '{typ}' must be 'stdio' or 'sse'.")
        if typ == "stdio" and not cfg.get("command"):
            r.err(f"tools/mcp.json: stdio server '{name}' needs a 'command'.")
        if typ == "sse":
            url = cfg.get("url", "")
            if not url:
                r.err(f"tools/mcp.json: sse server '{name}' needs a 'url'.")
            elif re.search(r"localhost|127\.0\.0\.1", url):
                r.err(f"tools/mcp.json: sse server '{name}' url uses localhost/127.0.0.1. "
                      f"From inside the agent's Docker sandbox that resolves to the container, "
                      f"not your machine — use http://host.docker.internal:<port>/sse.")
            else:
                r.ok(f"tools/mcp.json: sse server '{name}' looks reachable from the sandbox.")
    return keys


def validate_pixi_toml(proj: Path, r: Report) -> None:
    p = proj / "pixi.toml"
    if not p.exists():
        r.warn("pixi.toml is missing. Agent Studio can scaffold one, but tool "
               "dependencies (including the runtime) won't resolve without it.")
        return
    if tomllib is None:
        r.note("tomllib unavailable (need Python 3.11+) — skipped deep pixi.toml check.")
        return
    try:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        r.err(f"pixi.toml does not parse as TOML: {e}")
        return

    project = data.get("project", {})
    if not project.get("name"):
        r.warn("pixi.toml: [project].name is empty.")
    if not project.get("channels"):
        r.warn("pixi.toml: [project].channels missing — add at least ['conda-forge', 'anaconda'].")
    if not project.get("platforms"):
        r.warn("pixi.toml: [project].platforms missing — include your build target "
               "(e.g. 'osx-arm64') or the solve will reject your machine.")

    # Find the runtime dependency in either table.
    blob = json.dumps(data)
    if "anaconda_agent_runtime" not in blob and "anaconda-agent-runtime" not in blob:
        r.err("pixi.toml does not declare anaconda_agent_runtime. The agent's tools "
              "import it for the @tool decorator; without it nothing loads.")
    else:
        r.ok("pixi.toml declares anaconda_agent_runtime.")
        # If it points at a local wheel, the wheel must exist.
        pypi = data.get("pypi-dependencies", {})
        rt = pypi.get("anaconda_agent_runtime") or pypi.get("anaconda-agent-runtime")
        if isinstance(rt, dict) and rt.get("path"):
            wheel = proj / rt["path"]
            if not wheel.exists():
                r.err(f"pixi.toml points the runtime at '{rt['path']}', but that wheel "
                      f"is not in the project. Put it under packages/ or switch to the "
                      f"PyPI dependency form.")
            else:
                r.ok(f"runtime wheel present at {rt['path']}.")


def validate_structure(proj: Path, r: Report) -> None:
    tools = proj / "tools"
    if tools.is_dir():
        has_modules = any(f.suffix == ".py" and f.name != "__init__.py" for f in tools.iterdir())
        if has_modules and not (tools / "__init__.py").exists():
            r.warn("tools/ has modules but no __init__.py — add an empty one so Python "
                   "treats it as a package.")
    skills = proj / "skills"
    if skills.is_dir():
        for sub in skills.iterdir():
            if sub.is_dir() and not (sub / "SKILL.md").exists():
                r.warn(f"skills/{sub.name}/ has no SKILL.md — it won't register as a skill.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Preflight-validate an Agent Studio project.")
    ap.add_argument("project", help="Path to the agent project directory (the folder with agent.yaml).")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = ap.parse_args(argv)

    proj = Path(args.project).expanduser().resolve()
    r = Report()
    if not proj.is_dir():
        print(f"✗ '{proj}' is not a directory.", file=sys.stderr)
        return 2

    print(f"Validating Agent Studio project: {proj}\n")
    validate_structure(proj, r)
    validate_agent_yaml(proj, r)
    validate_pixi_toml(proj, r)
    # mcp.json is validated as a side effect of capability cross-checking, but
    # run it standalone too so a project with mcp.json and no agent.yaml refs is checked.
    _mcp_json_keys(proj, r)

    print(r.render())
    failed = r.n_err > 0 or (args.strict and r.n_warn > 0)
    print("\nRESULT:", "FAIL — fix the errors above before loading into Agent Studio."
          if failed else "PASS — safe to load into Agent Studio.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
