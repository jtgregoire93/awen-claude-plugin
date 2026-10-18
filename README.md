# Awen for Claude

Claude plugin for running an [Awen](https://awen.press) beta-read. An author
shares a review link from awen.press. Claude reads the manuscript one section
at a time, in the order Awen sets, and submits ratings that Awen checks
against the book's rubric before it releases the next section.

Beta-reader role only.

## Requirements

[uv](https://docs.astral.sh/uv/getting-started/installation/) must be on your
`PATH`. The plugin starts a local MCP server with it. uv installs Python 3.12
itself if you don't have it.

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

On first start, uv downloads the dependencies pinned in `uv.lock` (`mcp`,
`httpx`, and what they need) from PyPI and keeps a virtual environment in the
plugin folder.

## Guarantees

Enforced in `src/awen_mcp/core.py` and covered by the tests:

- Request URLs are built from a fixed template plus a token parsed out of a
  link on the configured origin. Redirects are never followed.
- The model never names a section. The server tracks position, and Awen gates
  the order.
- Payloads must be plain JSON under 64 KB. Everything else is Awen's
  validation.
- No open port, OAuth, database, or generic HTTP tool.

## Config

`AWEN_BASE_URL` sets the Awen origin. Default `https://awen.press`. It must be
https, except `http://localhost` for development.

## Development

```sh
uv sync
uv run pytest
uv run ruff check .
claude plugin validate .
claude --plugin-dir .   # load this checkout in Claude Code
```

## License

MIT. See [LICENSE](LICENSE).
