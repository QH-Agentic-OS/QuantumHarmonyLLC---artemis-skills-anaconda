# QuantumHarmonyLLC---artemis-skills-anaconda

Anaconda Agent Studio skills from the Artemis City project.

This repo holds skills authored for [Anaconda Agent Studio](https://www.anaconda.com/docs/tools/anaconda-desktop/agent-studio/main). Each skill is also format-compatible with Claude (same SKILL.md frontmatter), so any skill in this repo can be used in both ecosystems.

## Skills

| Skill | What it does |
|---|---|
| [`artemis-transmission-protocol`](./artemis-transmission-protocol) | Wraps agent communication in a normalized ATP header so multi-agent systems share a common envelope. Includes the `ArtemisPersona` class for mode-aware response framing. |

More to come as Artemis City components migrate over (validators, reflection, semantic tagging as standalone skills).

## Installing a skill in Anaconda Agent Studio

The Agent Studio UI imports skills directly from a public GitHub repo. Once this repo is pushed to GitHub:

1. Open Anaconda Desktop → enable **Agent Studio** under Beta features.
2. Launch Agent Studio → **Add-ons** → **Skills** → **Add**.
3. Enter:
   - **Owner**: `<your-github-username>` (e.g. `apollo92`)
   - **Repository**: `artemis-skills-anaconda`
   - **Skill name**: `artemis-transmission-protocol` (or leave blank to import every skill in the repo)
4. **Add to Catalog.**
5. (Recommended) Select the skill in the catalog → **Security** → **Start scan**. Enable **Deep scan with AI** if a provider is configured.
6. To enable the skill on an agent: open the agent's config page → **Add Capability** → **Skill** → check the box → **Save**.

## Installing a skill in Claude

The same `SKILL.md` works in Claude without modification. Drop the skill folder into wherever your Claude environment expects skills (typically `~/.claude/skills/<name>/`) or install via Claude's skill upload UI.

## Skill structure

Each skill folder follows the standard layout:

```
<skill-name>/
├── SKILL.md         # required: frontmatter (name, description) + body
├── references/      # loaded on demand
│   ├── *.md         # additional Markdown context
│   └── *.py         # Python modules the skill points the agent at
├── scripts/         # optional: executable helpers
└── assets/          # optional: templates, fonts, images
```

The `SKILL.md` frontmatter requires `name` and `description`. The description is the primary trigger mechanism — the agent reads it to decide whether to consult the skill.

## Authoring a new skill

1. Create a folder under the repo root.
2. Add a `SKILL.md` with valid frontmatter.
3. Put reference material in `references/` and point the body at it.
4. Commit, push, re-import in Agent Studio.

See [`artemis-transmission-protocol/SKILL.md`](./artemis-transmission-protocol/SKILL.md) as a worked example.

## License

MIT. See [LICENSE](./LICENSE).
