# Awen for Claude

Claude plugin for running an [Awen](https://awen.press) beta-read. An author
shares a review link from awen.press. Claude reads the manuscript one section
at a time, in the order Awen sets, and submits ratings that Awen checks
against the book's rubric before it releases the next section. The author sees
the ratings and notes on awen.press.

Beta-reader role only.

## Requirements

Python 3.9 or later, as `python3` on your `PATH`. On macOS it comes with the
Xcode Command Line Tools. The server is one file of standard-library Python,
so nothing is installed or downloaded.

It's a local (stdio) MCP server, so it runs in Claude Code and Cowork. In
claude.ai chat the skill loads but the server doesn't, and Claude will say so.

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
read starts at section 1. If Claude Code restarts partway through, the next
read starts over as a new reader.

## Tools

| Tool | Does |
|---|---|
| `start_review(session_url, model, name?)` | Registers as a beta-reader; returns rules, rubric, schema |
| `get_next_section()` | Fetches the section Awen says is next |
| `submit_checkpoint(payload)` | Posts ratings for that section; Awen validates |

## What it sends, and where

The server talks to one host: `https://awen.press`, or `AWEN_BASE_URL` if you
set it. It makes no other network calls, runs no models, and writes nothing to
disk.

Sent to Awen:

- the token from the review link, as part of each request path
- the model name and the reviewer name Claude passes to `start_review`
- the ratings and notes Claude writes for each section

Received from Awen:

- the book title, review rules, rubric, and submission schema
- the manuscript sections the author shared, one at a time

The session token and reviewer token stay in process memory. They are redacted
from every result and error returned to Claude, and they are gone when the
server exits. What Awen does with a review once it arrives is covered by the
[Awen privacy policy](https://awen.press/privacy).

## Troubleshooting

| You see | What it means |
|---|---|
| The `awen` tools are missing, or the server won't start | `python3` isn't on your `PATH`. Install Python 3.9+ (on macOS, `xcode-select --install`) and restart Claude Code. |
| `session_url must be an Awen review link` | Paste the full `https://awen.press/review/...` link the author shared. |
| `HTTP 404` with `session not found` | The link is mistyped, or the author deleted the book. |
| `HTTP 410` with `session expired or revoked` | Review links last 30 days after the book is rendered. Ask the author for a new one. |
| `Could not verify Awen's TLS certificate` | Your Python has no CA certificates. On a python.org macOS install, run `Install Certificates.command`. |
| `Could not reach Awen` | No network connection to awen.press. Check your connection and try again. |
| `HTTP 422` while submitting | The ratings didn't match the schema. Claude fixes what the error names and resends. |

## Support

- Bugs and questions: [GitHub issues](https://github.com/jtgregoire93/awen-claude-plugin/issues)
- Email, including security reports: support@awen.press

## Guarantees

Enforced in `server/awen_mcp.py` and covered by the tests:

- Request URLs are built from a fixed template plus a token parsed out of a
  link on the configured origin. Redirects are never followed.
- The model never names a section. The server tracks position, and Awen gates
  the order.
- Payloads must be plain JSON under 64 KB. Everything else is Awen's
  validation.
- No open port, OAuth, database, or generic HTTP tool. No proxy settings are
  read from the environment.

## Config

`AWEN_BASE_URL` sets the Awen origin. Default `https://awen.press`. It must be
https, except `http://localhost` for development.

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
