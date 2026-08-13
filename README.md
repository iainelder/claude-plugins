# claude-plugins

Iain Elder's personal Claude Code marketplace.

One marketplace (`iainelder`) containing one plugin (`iainelder`), which holds portable
skills that are useful in any repository.

## Skills

Just one to start: [`reading-github-issue-images`](plugins/iainelder/skills/reading-github-issue-images/SKILL.md).

## Install via marketplace

Two commands. The first registers the catalog; the second installs from it.

```bash
claude plugin marketplace add iainelder/claude-plugins
claude plugin install iainelder@iainelder
```

Skills are namespaced by the plugin, so this installs `/iainelder:reading-github-issue-images`.

Refresh later with `claude plugin marketplace update iainelder`, or turn on background
auto-update in `/plugin` (it is off by default for third-party marketplaces).

## Install without marketplace

If you are in a corporate environment and subject to [Claude Code's managed
settings](https://code.claude.com/docs/en/settings), they may restrict which
marketplaces may be added, via `strictKnownMarketplaces`. That restricts
*marketplaces*; it does not restrict the skills directory. Any folder under
`~/.claude/skills/` containing a `.claude-plugin/plugin.json` loads as a plugin
named `<name>@skills-dir` on the next session, with no marketplace and no
install step — and it is discovered in place, so a symlink into a git clone
works.

```bash
git clone https://github.com/iainelder/claude-plugins.git
mkdir -p ~/.claude/skills
ln -s "$PWD"/claude-plugins/plugins/iainelder ~/.claude/skills/iainelder
```

This loads as `iainelder@skills-dir`, with the same `/iainelder:` invocation prefix as
the marketplace install. Keep the symlink's name identical to the plugin's manifest name.

Symlink the **plugin** directory, not individual skills. New skills added to the
plugin then appear from a `git pull` alone, with nothing to set up on that machine.

Confirm it loaded:

```bash
claude plugin list
claude plugin details iainelder@skills-dir
```

Do not use both installation methods on one machine: `iainelder@iainelder` and
`iainelder@skills-dir` would both load, and every skill would appear twice.

### Keeping it current

Skills-directory plugins have no auto-update.

Use `git pull` to update, either in a background service or a Claude `SessionStart` hook.

Later I'll figure out how to do that and show it here.

## Naming

The marketplace name and the plugin name exist in a global namespace where they
are installed, so my GitHub username is a cheap way to make it unique.

## Development

Clone the repo and load it directly, without touching the installed copy:

```bash
git clone https://github.com/iainelder/claude-plugins.git ~/tmp/dev
claude --plugin-dir ~/tmp/dev/plugins/iainelder
```

A `--plugin-dir` plugin takes precedence over an installed plugin of the same name for
that session. Run `/reload-plugins` to pick up edits without restarting.

Never edit the versions in `~/.claude/plugins/marketplaces/`. Claude Code manages its own copy from the marketplace and will overwrite your edits without warning when it syncs new versions.

Validate before pushing:

```bash
claude plugin validate .
claude plugin validate ./plugins/iainelder
```
