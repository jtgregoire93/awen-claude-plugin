# Awen for Claude

Claude plugin for running an [Awen](https://awen.press) beta-read. An author
shares a review link from awen.press. Claude reads the manuscript one section
at a time, in the order Awen sets, and submits ratings that Awen checks
against the book's rubric before it releases the next section. The author sees
the ratings and notes on awen.press.

Beta-reader role only.

## Requirements

Nothing to install. The plugin connects to Awen's hosted MCP server at
`https://awen.press/mcp`, so it works in Claude Code, Cowork, and claude.ai
on the web, desktop and mobile.

On claude.ai you can also add the server yourself as a custom connector:
Settings → Connectors → Add custom connector, URL `https://awen.press/mcp`,
no authentication.

## Install

In Claude Code (terminal, desktop app or IDE), add this repo as a plugin
marketplace and install from it:

```text
/plugin marketplace add https://github.com/jtgregoire93/awen-claude-plugin.git
/plugin install awen@awen-press
```

Run `/plugin marketplace update awen-press` to pick up new versions. On
claude.ai (web, desktop, mobile), add the custom connector above instead.

## Use

Give Claude the author's review link. You don't need an account or an API key;
the link is the only credential. Some prompts that work:

```text
Run an Awen beta-read: https://awen.press/review/<token>
```

```text
Here's my Awen review link: https://awen.press/review/<token>
Do the beta-read and sign your notes as "Claude".
```

```text
Beta-read this book on Awen, then summarize what you flagged in each
section: https://awen.press/review/<token>
```

The `awen-review` skill walks Claude through the loop: start the read, fetch a
section, submit ratings for it, repeat until Awen says the read is done. Each
read starts at section 1. `start_review` returns a `review` value that Claude
passes to the other two tools; as long as Claude still has it, the read
carries on after a reconnect or in a later message. A read with no calls for
24 hours ends, and Claude starts a new one.

## Tools

| Tool | Does |
|---|---|
| `start_review(session_url, model, name?)` | Registers as a beta-reader; returns rules, rubric, schema, and the `review` value |
| `get_next_section(review)` | Fetches the section Awen says is next |
| `submit_checkpoint(review, payload)` | Posts ratings for that section; Awen validates |

## What it sends, and where

Claude talks to one host: `https://awen.press/mcp`. The plugin runs no code
on your machine, makes no other network calls, and writes nothing to disk.

Sent to Awen:

- the review link, inside the `start_review` call
- the model name and the reviewer name Claude passes to `start_review`
- the `review` value on each later call
- the ratings and notes Claude writes for each section

Received from Awen:

- the book title, review rules, rubric, and submission schema
- the manuscript sections the author shared, one at a time
- the `review` value for this read

For each read, Awen stores the reviewer name and model name, the ratings and
notes, and the read's place (section number, and whether the current section
was fetched). The `review` value is stored only as a SHA-256 hash. The read's
place is deleted 24 hours after its last call, 7 days after it started, or
when the author's link expires, whichever comes first. The link token and the
reviewer token are never returned to Claude; both are redacted from every
result and error. What Awen does with a review once it arrives is covered by
the [Awen privacy policy](https://awen.press/privacy).

## Troubleshooting

| You see | What it means |
|---|---|
| The `awen` tools are missing | The plugin or connector isn't enabled, or `https://awen.press/mcp` is unreachable. Check your connection and reload the plugin or connector. |
| `session_url must be an Awen review link` | Paste the full `https://awen.press/review/...` link the author shared. |
| `HTTP 404` with `session not found` | The link is mistyped, or the author deleted the book. |
| `HTTP 403` with `AI reviews need the Author Hub` | The book doesn't have the Author Hub add-on. The author can add it on awen.press. |
| `HTTP 410` with `session expired or revoked` | Review links last 30 days after the book is rendered. Ask the author for a new one. |
| `No active review for that value` | The read ended (24 hours without a call) or the `review` value was mistyped. Start a new read with the link. |
| `Too many calls` or `too many reads` | Awen's rate limits. Wait a minute (calls) or an hour (new reads on one link). |
| `HTTP 422` while submitting | The ratings didn't match the schema. Claude fixes what the error names and resends. |

## Support

- Bugs and questions: [GitHub issues](https://github.com/jtgregoire93/awen-claude-plugin/issues)
- Email, including security reports: support@awen.press

## Guarantees

Enforced by Awen's hosted server:

- The only link it accepts is an Awen review link on its own origin. It
  fetches no URLs, so nothing can redirect it.
- The model never names a section. Awen tracks position and gates the order.
- Payloads must be plain JSON under 64 KB. Everything else is Awen's
  validation.
- No OAuth and no accounts. Browser origins other than awen.press and
  claude.ai are refused.

## Local fallback

`server/awen_mcp.py` is the earlier local (stdio) server, kept for offline or
self-hosted use. It is one file of standard-library Python 3.9+, holds the
read in process memory, and calls Awen's review API at `https://awen.press`
(or `AWEN_BASE_URL`, which must be https except `http://localhost`). Its
tools take no `review` value. To use it instead of the hosted server, add
this to a project's `.mcp.json`:

```json
{
  "mcpServers": {
    "awen-local": {
      "command": "python3",
      "args": ["-I", "/path/to/awen-claude-plugin/server/awen_mcp.py"]
    }
  }
}
```

On a python.org macOS install with no CA certificates, run
`Install Certificates.command` first.

## Development

The dev tools (pytest, ruff, and the official MCP client for an interop test)
are managed with uv. Users don't need any of them.

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate .
claude --plugin-dir .   # load this checkout in Claude Code
```

## License

MIT. See [LICENSE](LICENSE).
