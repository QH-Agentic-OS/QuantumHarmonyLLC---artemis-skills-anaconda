# Changelog

## 1.1.0
- Fixed `persona.py` reference from a hardcoded absolute path to the bundled `scripts/persona.py`
  (portable import via `CLAUDE_SKILL_DIR`).
- Corrected schema path from `references/atp_schema.sql` to `assets/atp_schema.sql`.
- Documented previously-undocumented resources: `reflection.py`, `semantic_tagging.py`,
  `assets/atp_registry.db`.
- Clarified that the registry ships pre-seeded (~29 tags); schema is for recreation/migration only.
- Added `license` (Apache-2.0) and version metadata to SKILL.md frontmatter.

## 1.0.0
- Initial Artemis Transmission Protocol skill.
