# Skills in Anaconda Agent Studio

The single best feature of Agent Studio's skill system, from a tooling-author perspective: **it reads the same SKILL.md format Claude does.** YAML frontmatter on top, Markdown body underneath, optional `references/`, `scripts/`, `assets/` directories alongside. One skill, two ecosystems.

This page covers the differences that *do* exist, because they're easy to miss.

## How Agent Studio discovers a skill

Three discovery paths, in roughly increasing order of "you'll use this":

1. **Bundled in the agent project** at `<agent>/skills/<skill-name>/SKILL.md`. Agent Studio reads this when the agent is loaded.

2. **Added from a public GitHub repo** via Add-ons → Skills → Add. You give it owner + repo, and optionally a specific skill name. The repo just needs a folder containing `SKILL.md`. Agent Studio fetches it into the global catalog.

3. **Inherited from a plugin.** Plugins (Atlassian, Miro, nteract, Omni) ship skills that auto-register. These are read-only — manage them through the plugin, not the Skills page.

The global catalog under Add-ons → Skills is shared across all agents on the machine. Bundled skills are scoped to one agent. Pick the right one based on reuse needs.

## The frontmatter

Same as Claude:

```markdown
---
name: my-skill
description: One-paragraph explanation of what this skill does AND when the agent should reach for it. The "when" is what the model uses to decide whether to load the skill at all — write it like you're writing a tool description for the model, not a marketing blurb for a human.
---

# My Skill

Body content here...
```

The fields Agent Studio actually uses:
- `name` (required) — the skill's identifier.
- `description` (required) — the trigger description. This is the only thing the model sees when deciding to consult the skill, so it has to do real work.

Other fields Claude accepts (`compatibility`, `license`, etc.) are tolerated but largely cosmetic in the current Agent Studio Beta.

## Description writing — same rules as Claude

This part transfers verbatim from the Claude skill-author guidance:

- Lead with "what it does" then "when to use it."
- Spell out the trigger contexts explicitly. "Use this when the user mentions X, Y, or Z" is much better than implicit hope.
- A little pushy beats a little shy. Skills tend to under-trigger; descriptions that name concrete scenarios pull their weight.
- If the skill shares keywords with another skill, distinguish them in the description.

A description that works in Claude works in Agent Studio. A description that fails to trigger in Claude will also fail in Agent Studio.

## Body content — what to put

The body is read into the agent's context when the skill triggers, exactly like Claude. Same patterns apply:

- Keep `SKILL.md` itself under ~500 lines; push deep detail into `references/` files that are loaded on demand.
- Explain *why*, not just *what* — the model is smart, it does better when it understands the reasoning.
- Avoid heavy MUSTs / ALWAYs unless absolutely necessary. Explain the constraint and the model will respect it.

The body can reference local files using relative paths. `references/atp_spec.md` resolves to `<skill-folder>/references/atp_spec.md`.

## Bundled scripts and assets

Agent Studio supports the same three-folder pattern Claude uses:

- `scripts/` — executable Python (or shell) used by the skill. Tools run them via the agent's runtime; they don't have to be `@tool`-decorated themselves if they're just helpers the skill invokes.
- `references/` — Markdown loaded into context only when the skill points the model at them.
- `assets/` — templates, images, fonts, anything used as output material.

For an Agent Studio agent, scripts in a skill folder are reachable from the sandbox at whatever path the runtime mounts the skill into. The path is stable; the docs don't publish it explicitly, but `<workdir>/.skills/<skill-name>/` is the conventional location. Test before relying.

## The security scanner — a real difference

This is the one feature that's Anaconda-only. Skills in the global catalog can be scanned by Add-ons → Skills → select skill → Security → Start scan.

What the scan does:
- **Offline pass (always):** static analysis, bytecode inspection, behavioral analysis. Flags dangerous code execution patterns, suspicious behavior, injection risks.
- **Deep scan with AI (optional):** sends the skill content to your configured AI provider for semantic analysis of intent. Requires a valid AI provider.

Severities: Critical, High, Medium, Low, None. Critical and High should block use until resolved.

**Recommend a scan for any skill imported from GitHub before enabling it on a real agent.** This is the kind of thing that's easy to skip and then regret.

## Migration from a Claude skill — the actual checklist

When the user has an existing Claude skill they want to use in Agent Studio:

1. Check the frontmatter has `name` and `description`. Fix if missing.
2. Confirm no Claude-specific tool names appear in the body (e.g., references to `bash_tool`, `str_replace`, etc., that won't exist in Agent Studio). If they do, rewrite to describe the *capability* not the *tool name* — let the agent's own tool set fulfill it.
3. Drop the folder into either:
   - `<agent-project>/skills/<name>/` (bundled), OR
   - a GitHub repo and add via owner/repo (catalog).
4. Run the security scan the first time.
5. Enable the skill on the agent: Capabilities → Add Capability → Skill → check the box.

That's the full migration. In most cases the only edit is step 2, and often there are no edits at all.

## Bundled vs catalog — picking right

| Scenario | Choose |
|---|---|
| Skill is specific to this one agent's purpose | Bundled |
| Skill is reused across multiple agents | Catalog |
| Skill is published / shared with collaborators | Catalog (via GitHub) |
| Skill is a work-in-progress, fast iteration | Bundled (no GitHub round-trip) |
| Skill ships as part of an agent template | Bundled |

## Anti-patterns specific to Agent Studio

- **Putting tool-call invocations in skill prose.** Skills describe *when and how* to call tools; they don't invoke them directly. The agent calls the tool; the skill is the instruction set.
- **Hardcoding paths from the host machine.** The agent runs in a Docker sandbox by default. `~/Documents/...` won't resolve. Reference mounted paths (`/work/input/...`) or environment variables, or describe the mount the agent needs.
- **Putting secrets in the skill body.** Skills travel with the agent project — they may go in version control, get shared, etc. Use the agent's env vars or AI provider config for anything sensitive.

## The ATP case (specific to this project)

The `artemis-transmission-protocol` skill in this same project is designed to be format-compatible with both Claude and Agent Studio. To migrate:

1. Copy `/mnt/skills/user/artemis-transmission-protocol/` into `<agent-project>/skills/atp/`.
2. Edit the `description` to add Agent Studio-relevant trigger phrases ("use when the agent needs to emit a structured ATP header before responding").
3. The `references/atp_schema.sql` and `references/persona.py` references travel with the skill.

The skill works unchanged. The Artemis personas (`Artemis-Oracle`, `Compsuite`, etc.) map cleanly: one Agent Studio agent per persona, each with the ATP skill enabled.
