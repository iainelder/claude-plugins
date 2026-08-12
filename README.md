# claude-plugins

Iain Elder's personal Claude Code marketplace.

One marketplace (`iainelder`) containing one plugin (`tools`), which holds portable
skills that are useful in any repository.

| Level | Value |
| :--- | :--- |
| Repository | `iainelder/claude-plugins` |
| Marketplace name | `iainelder` |
| Plugin name | `tools` |
| Skills | `read-github-issues-images` |

The marketplace name is deliberately **not** the same as the repository name, so the
install commands below are the source of truth — copy them rather than deriving the
name from the repository.

## Install where marketplaces are permitted

Two commands. The first registers the catalog; the second installs from it.

```bash
claude plugin marketplace add iainelder/claude-plugins
claude plugin install tools@iainelder
```

Skills are namespaced by the plugin, so this installs `/tools:read-github-issues-images`.

Refresh later with `claude plugin marketplace update iainelder`, or turn on background
auto-update in `/plugin` (it is off by default for third-party marketplaces).

## Install where this marketplace is not on the allowlist

Managed settings can restrict which marketplaces may be added, via
`strictKnownMarketplaces`. That restricts *marketplaces*; it does not restrict the
skills directory. Any folder under `~/.claude/skills/` containing a
`.claude-plugin/plugin.json` loads as a plugin named `<name>@skills-dir` on the next
session, with no marketplace and no install step — and it is discovered in place, so
a symlink into a git clone works.

```bash
git clone https://github.com/iainelder/claude-plugins.git ~/repos/claude-plugins
mkdir -p ~/.claude/skills
ln -s ~/repos/claude-plugins/plugins/tools ~/.claude/skills/tools
```

This loads as `tools@skills-dir`, with the same `/tools:` invocation prefix as the
marketplace install. Keep the symlink's name identical to the plugin's manifest name.

Symlink the **plugin** directory, not individual skills. New skills added to the
plugin then appear from a `git pull` alone, with nothing to set up on that machine.

Confirm it loaded:

```bash
claude plugin list
claude plugin details tools@skills-dir
```

Do not use both installation methods on one machine: `tools@iainelder` and
`tools@skills-dir` would both load, and every skill would appear twice.

### Keeping it current

Skills-directory plugins have no auto-update — that is a marketplace feature — so
`git pull` is the update mechanism. A systemd user timer running
`git -C ~/repos/claude-plugins pull --ff-only` avoids adding latency to every session
start. A `SessionStart` hook works too, if pull-on-use suits the machine better.

Edits to a `SKILL.md` take effect in the current session. Changes to other plugin
components need `/reload-plugins` or a restart.

## Development

Edit this checkout and load it directly, without touching the installed copy:

```bash
claude --plugin-dir ~/Repos/claude-plugins/plugins/tools
```

A `--plugin-dir` plugin takes precedence over an installed plugin of the same name for
that session. Run `/reload-plugins` to pick up edits without restarting.

Never edit `~/.claude/plugins/marketplaces/iainelder/` — Claude Code owns that clone
and overwrites it on update.

Validate before pushing:

```bash
claude plugin validate .
claude plugin validate ./plugins/tools
```
