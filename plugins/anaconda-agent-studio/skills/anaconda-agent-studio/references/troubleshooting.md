# Troubleshooting — error recovery by layer

When an Agent Studio build fails, the app usually surfaces one terse line. The
real cause is almost always in one of seven layers below. Work top-down: a
problem in an earlier layer (the app won't open, the env won't solve) masks
everything under it, so fix in order.

Provenance is marked: **[docs]** = from Anaconda's published troubleshooting /
product docs; **[operational]** = standard platform behavior + field experience,
not a doc-sourced Agent-Studio-specific entry. Treat [operational] as a strong
default, but if it doesn't match, re-fetch the current docs (the product is Beta
and moves).

Quick index:
- A. Desktop / Agent Studio won't open or install
- B. macOS code signing & Gatekeeper (the unsigned-binary / keychain class)
- C. conda / pixi build layer (environment won't resolve)
- D. Docker / sandbox
- E. agent.yaml & capabilities won't load
- F. MCP / SSE / orchestration
- G. Skills

Before reading: the fastest triage is `python scripts/validate_agent.py <project>`.
It catches every layer-C/E/F config error statically. Run it first.

---

## A. Desktop / Agent Studio won't open or install

### Agent Studio option isn't visible
**Cause:** BETA Features not enabled. **Fix:** Settings → enable **BETA Features**
→ toggle **Agent Studio** on → it downloads/installs on first open (accept the
Privacy Policy / ToS). **[docs]**

### Anaconda Desktop won't open — silent failure (Linux)
Two common causes. **[docs]**
- **Wayland.** Desktop is Electron and can't render under Wayland. Check with
  `echo $XDG_SESSION_TYPE`; if it prints `wayland`, launch with
  `anaconda-desktop --ozone-platform=x11`.
- **Keyring out of sync.** The login keyring no longer matches your user
  password — typically because the password was changed via `passwd` in a
  terminal rather than through system settings, which bypasses the PAM hook that
  re-syncs the keyring. Run `anaconda-desktop` from a terminal and look for
  keyring errors; if present, delete the login keyring so it regenerates:
  `rm ~/.local/share/keyrings/login.keyring` (GNOME) or
  `rm ~/.local/share/kwalletd/kdewallet.kwl` (KDE), then log out and back in.
  *(This is the same failure shape as a desynced macOS login keychain — see B.)*

### Model won't load, exit code 3221225781 (Windows)
**Cause:** the model needs a C++ runtime Windows doesn't ship. **Fix:** install
the latest Microsoft Visual C++ Redistributable. **[docs]**

### "Unable to retrieve local user environment" (Windows)
**Cause:** Windows' 260-char path limit truncates the nested
`%USERPROFILE%\.anaconda-desktop\micromamba\envs\pkgs\` path; micromamba aborts
with `Invalid package cache` / `INSTALL_FAILED`. **Fix:** enable Win32 long paths
(Group Policy → *Enable Win32 long paths*, or registry `LongPathsEnabled = 1`
under `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem`), reboot, delete the
contents of that `pkgs` folder, restart the app. If it persists, delete the whole
`micromamba` folder and let it rebuild. **[docs]**

---

## B. macOS code signing & Gatekeeper (unsigned binary / keychain class)

This is the cluster behind "repeated Gatekeeper prompts about Python," a binary
that "can't be opened because the developer cannot be verified," and a login
keychain that keeps re-prompting. The trigger is usually an **unsigned or
quarantined binary in the environment** (a conda/pixi-installed Python or a
tool's native dependency that didn't come signed). **[operational]**

### Diagnose
```bash
spctl -a -vvv /path/to/binary           # Gatekeeper's verdict (rejected = unsigned/quarantined)
codesign -dv --verbose=4 /path/to/binary 2>&1 | sed -n '1,12p'   # signature, or lack of one
xattr -p com.apple.quarantine /path/to/binary 2>/dev/null && echo "quarantined"
```

### Fix — least invasive first
1. **Strip the quarantine flag** on the binary or the whole env directory:
   ```bash
   xattr -dr com.apple.quarantine ~/path/to/env
   ```
2. **Ad-hoc re-sign** if it's unsigned and you trust it:
   ```bash
   codesign --force --deep --sign - /path/to/binary
   spctl -a -vvv /path/to/binary   # re-check
   ```
3. **Prefer reinstalling from a signed source** over fighting per-binary. A fresh
   miniconda / pixi env installed normally (not copied or restored from an
   archive that lost xattrs) generally comes through Gatekeeper cleanly. Recreate
   the env rather than patching dozens of binaries one at a time.

### The keychain link
If stripping quarantine doesn't stop a *login-keychain* prompt loop, the keychain
itself is likely desynced from your account password — same root cause as the
Linux keyring case in A: a password changed outside the normal flow leaves the
keychain encrypted under the old password. Fix at the OS layer: in **Keychain
Access**, reset the **login** keychain (or change its password to match your
account), then reboot. Don't keep dismissing the prompts — each dismissal can
leave the agent's credential reads failing silently. **[operational]**

> If you're on an **Intel Mac**: Anaconda has dropped `osx-64` Desktop/installer
> support; a failing `.pkg` may simply be the wrong architecture. Pull an
> `osx-64` build from the installer archive, or expect issues. **[docs]**

---

## C. conda / pixi build layer (environment won't resolve)

Symptoms here show up as a `pixi install` failure in the terminal (if you
followed `build_and_run.md` step 2) or a generic "environment" error in the app.

### `command not found: conda` / `pixi`
**Cause:** not initialized on PATH. **Fix:** restart the shell after install, or
`source ~/.zshrc` (zsh) / `~/.bashrc` (bash); for conda, `conda init` from its
`bin/`. **[docs]**

### `pixi install` won't solve / `PackagesNotFoundError`
**Causes & fixes:** **[docs/operational]**
- Channels missing — `pixi.toml [project].channels` should include
  `["conda-forge", "anaconda"]`.
- Your platform isn't listed — add it to `[project].platforms` (e.g.
  `osx-arm64`), or the solver rejects your machine.
- Over-tight pin — loosen, e.g. `python = ">=3.11,<3.13"`.
- Typo'd package name, or it's not on your channels for your OS/arch.
- Stale lock after edits — remove `pixi.lock` and re-run `pixi install`.

### `anaconda_agent_runtime` not found
**Cause:** the `[pypi-dependencies]` entry points at a wheel path that isn't
there, or the PyPI form is commented out. **Fix:** confirm the wheel is in
`packages/` and the `path` matches, or switch to `anaconda_agent_runtime = ">=0.1.0"`.
The validator flags this. **[operational]**

### `EnvironmentNotWriteableError` / permission denied
**Cause:** building in a protected/admin-owned dir. **Fix:** build the project in
a directory you own (home, not `/opt`). **[docs]**

### `Collecting package metadata … Killed`
**Cause:** out of memory/disk during the solve. **Fix:** free space/RAM; check
system requirements. **[docs]**

### `CondaHTTPError: HTTP 400/404 for channel`
**Cause:** a typo'd channel URL/name. **Fix:** `conda config --show channels`,
remove the bad one. **[docs]**

---

## D. Docker / sandbox

### "Docker Desktop not running / not installed"
**Cause:** `sandbox.enabled: true` (the default) requires Docker. **Fix:** install
Docker Desktop and start it before running the agent — or set `sandbox.enabled:
false` for trusted local dev. **[operational]**

### A tool or MCP server can't reach a service on your machine
**Cause:** `localhost` / `127.0.0.1` inside the container points at the container,
not the host. **Fix:** use `http://host.docker.internal:<port>` for any host
service. This is the single most common sandbox bug; the validator errors on it
in `tools/mcp.json`. **[operational]**

### Mounted folder isn't visible to the agent
**Cause:** not mounted, or mounted at a different `sandbox_path`. **Fix:** add an
explicit `sandbox.mounts` entry; remember the agent only sees what you mount, and
default to `ro`. **[operational]**

### Agent can't make outbound calls
**Cause:** `sandbox.network: isolated`. **Fix:** set `network: outbound` if the
agent legitimately needs to call APIs/MCP servers. **[operational]**

---

## E. agent.yaml & capabilities won't load

### Project won't load at all
**Cause:** `agent.yaml` doesn't parse — almost always a **tab character** or a
misaligned indent (YAML requires spaces). **Fix:** run the validator; it points
at the parse error. **[operational]**

### Provider/model shows red / "provider not found"
**Cause:** `ai_provider.provider` or `model` doesn't match a provider configured
in **AI Providers** exactly; or, for `anaconda-desktop`, no local model server is
running. **Fix:** match the names exactly; start the Desktop model server for
local providers. **[operational]**

### A tool doesn't appear in the agent's tool list
**Causes & fixes:** **[operational]**
- The module didn't import — a dependency it imports isn't in `pixi.toml`
  (resolve it: `pixi add <pkg>`), or `tools/__init__.py` is missing.
- The function isn't decorated with `@tool`.
- Exotic type hints degraded the schema — flatten to primitives
  (`tool_authoring.md` → type hints).

### The agent describes a tool action instead of doing it
**Causes & fixes:** **[operational]**
- Weak docstring — the model can't tell when to call it. Lead with a present-tense
  verb; make `Args:`/`Returns:` concrete (`tool_authoring.md`).
- The tool's approval is `disabled`, or stuck on `ask` and the prompt was
  dismissed.

---

## F. MCP / SSE / orchestration

### SSE connection refused / agent B not reachable
**Causes & fixes:** **[operational]**
- Target agent/Tool Server isn't running — start it first.
- Wrong port — copy the URL fresh from the target's **Connect** dialog.
- `localhost` used from inside a sandbox — use `host.docker.internal` (see D).

### Agent B's individual tools aren't visible from agent A
**Not a bug.** Only B's conversational interface is exposed over MCP, by design —
A sees B as one tool. To expose primitives, build a **Tool Server**, not an
agent. **[operational]**

### A stdio MCP server fails to launch
**Cause:** `command` not on PATH, wrong `args`, or wrong `cwd`. **Fix:** verify the
command runs in a plain shell; check `tools/mcp.json` fields. **[operational]**

---

## G. Skills

### A skill doesn't trigger
**Causes & fixes:** **[operational]**
- Not listed in `agent.yaml` `capabilities.skills`.
- The `skills/<name>/` folder is missing `SKILL.md`, or its frontmatter lacks
  `name`/`description`.
- The `description` is too narrow — broaden it to name the contexts/phrasings
  that should trigger it (`skills_in_anaconda.md`).

### An imported skill is flagged by the security scan
**Cause/Fix:** Agent Studio scans imported skills. Read the scanner output, remove
the flagged content (or confirm it's a false positive), re-scan before enabling.
**[docs]**

---

## When none of this matches

The product is Beta. If a failure isn't covered here, re-fetch the current docs
(`anaconda.com/docs/llms.txt` lists every page) and the in-app **Feedback**
button routes to the team. Then update this reference and the `Source` note in
`SKILL.md` — the whole skill is built to be re-grounded as the product changes.
