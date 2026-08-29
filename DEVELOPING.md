# Developing

Notes for anyone working on `uukanshu` itself. The [README](README.md) covers
the reader-facing side; [RELEASING.md](RELEASING.md) covers cutting releases.

## Project layout

| Path                            | What it is                                                                |
| ------------------------------- | ------------------------------------------------------------------------- |
| `src/uukanshu/__init__.py`      | The whole app in one module: fetching, HTML parsing, reader UI, CLI       |
| `pyproject.toml`                | Package metadata, dependencies, the `uukanshu` console entry point        |
| `uukanshu.spec`                 | PyInstaller spec for the standalone release binaries                      |
| `.github/workflows/release.yml` | Release pipeline: per-platform binary builds attached to a GitHub Release |
| `uv.lock` / `.python-version`   | Pinned dependency and Python (3.14) versions — shared with CI             |

Inside the module, the pieces are:

- `fetch()` — HTTPS via `urllib.request` with browser-like headers, gzip
  decoding, retries with backoff, and a `certifi` TLS context. **The TLS
  context matters**: see the TLS fingerprinting note below.
- `chapter_list()` / `extract_chapter()` — regex-based parsing of the site's
  TOC and chapter pages.
- `TocScreen` / `Reader` — the Textual UI (modal chapter picker, reader pane,
  themes, OpenCC conversion).
- `run()` / `main()` — argparse CLI.

## Setting up a development environment

Install [uv](https://docs.astral.sh/uv/), then:

```sh
git clone https://github.com/edisoncks/uukanshu && cd uukanshu
uv sync --group build        # project + dependencies + PyInstaller
uv run uukanshu --help
```

`uv.lock` is committed: after changing dependencies with `uv add` / `uv
remove`, commit the updated lock alongside `pyproject.toml`.

## Daily-use install from source

To have the `uukanshu` command without a binary (auto-upgradable):

```sh
uv tool install .                                   # from a local clone
uv tool install git+https://github.com/edisoncks/uukanshu   # or from git
uv tool upgrade uukanshu                            # after pulling changes
uv tool uninstall uukanshu
```

If the command isn't found afterwards: `uv tool update-shell`, then restart
the shell.

## Building binaries

PyInstaller cannot cross-compile, so build **on** the target platform:

```sh
uv run --no-sync pyinstaller uukanshu.spec --noconfirm
# → dist/uukanshu (dist/uukanshu.exe on Windows)
```

Then smoke-test the artifact — a real fetch, not just `--help`:

```sh
./dist/uukanshu --book 18957 --list
```

### TLS fingerprinting

uukanshu.cc sits behind Cloudflare, which scores clients on their TLS
handshake. Empirically, binaries built with some Python toolchains get 403
blocked from residential IPs while others pass — the frozen OpenSSL's
ClientHello differs per build. That's why:

- CI builds with **the same uv-managed Python 3.14 toolchain** that local
  builds are verified with (`.python-version` + committed `uv.lock`).
- The release pipeline's smoke test performs a **real fetch**, so a build
  whose fingerprint is blocked fails the workflow instead of shipping.
- `certifi` is a runtime dependency and `fetch()` uses its CA store: frozen
  binaries don't reliably see the system CA store.

If blocking ever becomes persistent rather than toolchain-specific, the
escape hatch is switching `fetch()` to a client that impersonates browser
TLS (e.g. `curl_cffi`), at the cost of a heavier dependency.

## Windows console encoding

`main()` forces stdout/stderr to UTF-8 (`_force_utf8_stdio()`): Windows
consoles default to a legacy codepage (e.g. cp1252) that cannot encode the
help text (arrows, CJK) or Chinese content. Don't remove it — the first
v0.1.0 CI run shipped exactly that crash.

## Releasing

Tag-driven and automated — see [RELEASING.md](RELEASING.md). In short: bump
`__version__` in `src/uukanshu/__init__.py`, commit, push a `v*` tag; CI
builds the three binaries and attaches them to a GitHub Release.
