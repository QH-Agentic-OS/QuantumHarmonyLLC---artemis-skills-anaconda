---
name: <skill-name-in-kebab-case>
description: <One paragraph. Lead with what the skill does, then spell out when the agent should reach for it. List specific trigger phrases the user might say. Be a little pushy — skills under-trigger by default. This description is the only thing the model sees when deciding whether to consult the skill, so make every word work. Example: "Scaffold and validate ATP (Artemis Transmission Protocol) headers. Use whenever the user mentions ATP, the Artemis Transmission Protocol, asks to format an inter-agent message with a header block, or requests structured agent-to-agent communication. Also use when the user pastes a raw prompt and asks you to 'turn this into ATP' or 'add the ATP header.'">
---

# <Skill Title in Title Case>

## Overview

One to three sentences answering "what is this skill for?" Don't repeat the frontmatter description verbatim — that's about *when to trigger*. This is about *what the skill does* once it's running.

## When to use which path

If the skill has multiple workflows, route to the right one here. Otherwise delete this section.

| User wants... | Read |
|---|---|
| To do X | `references/x_guide.md` |
| To do Y | `references/y_guide.md` |
| The full spec | `references/spec.md` |

## Core instructions

The main body of guidance the agent needs to act. Keep it under ~250 lines if you can; push deep detail into `references/`.

Tips:
- Use imperative voice ("Do X" not "You should do X").
- Explain *why*, not just *what*. The agent does better when it understands the reason.
- Show examples for non-obvious patterns.

## Examples

**Example 1 — <one-line context>:**

Input: <what the user says>
Output: <what the agent does>

**Example 2 — <one-line context>:**

Input: ...
Output: ...

## Anti-patterns

Things to NOT do. List them. The negative case often teaches faster than the positive case.

## Resources

### references/
- `references/<file>.md` — what's in it, when to load it.

### scripts/
- `scripts/<file>.py` — what it does, how to invoke it.

### assets/
- `assets/<file>` — what it is, what it's used for.

<!--
Format compatibility notes (delete this comment before shipping):
- This file works unchanged in both Claude and Anaconda Agent Studio.
- For Agent Studio: drop the folder containing this SKILL.md into either
  <agent>/skills/<name>/ (bundled) or a GitHub repo + Add-ons → Skills → Add.
- For Claude: place under ~/.claude/skills/<name>/ or upload via skills UI.
- The agent triggers on the description; the body loads when triggered;
  references/, scripts/, assets/ load on demand.
-->
