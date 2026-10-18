# Awen for Claude

Claude plugin for running an [Awen](https://awen.press) beta-read. An author
shares a review link from awen.press. Claude reads the manuscript one section
at a time, in the order Awen sets, and submits ratings that Awen checks
against the book's rubric before it releases the next section.

Beta-reader role only.

## Requirements

Python 3.9 or later, as `python3` on your `PATH`. On macOS it comes with the
Xcode Command Line Tools. The server is one file of standard-library Python,
so nothing is installed or downloaded.

It's a local (stdio) MCP server, so it runs in Claude Code and Cowork. It
doesn't run in claude.ai chat.

## Use

Give Claude the author's review link:

```text
Run an Awen beta-read: https://awen.press/review/<token>
```

The `awen-review` skill walks Claude through the loop. You don't need an
account or an API key. The link is the only credential.

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
are managed with [uv](https://docs.astral.sh/uv/). Users don't need any of
them.

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate .
claude --plugin-dir .   # load this checkout in Claude Code
```

## License

MIT. See [LICENSE](LICENSE).
