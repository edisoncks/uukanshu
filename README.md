# uukanshu

Read novels from [uukanshu.cc](https://uukanshu.cc) directly in your terminal.

`uukanshu` fetches chapters over plain HTTPS using only the Python standard
library, strips the page down to just the chapter text, optionally converts
Traditional → Simplified Chinese via [OpenCC](https://github.com/BYVoid/OpenCC),
and presents it in a clean, CJK-aware reading pane built with
[Textual](https://github.com/Textualize/textual).

---

## Features

- 📖 **Comfortable reader UI** — reflowing text with CJK-aware padding that
  stays correct on all four sides, even as you resize the terminal
- 🧭 **In-app navigation** — jump between chapters, or browse the full
  chapter list with a searchable, instantly-opening picker
- 🀄 **Simplified / Traditional toggle** — convert the entire chapter (text,
  titles, and UI) on the fly, without refetching
- 🎨 **8 color themes** — night, sepia, paper, three Catppuccin variants,
  Tokyo Night, and Matrix
- 🖨️ **Plain-text mode** — dump a clean chapter to stdout for piping or saving
- 📦 **Easy install** — one command installs the `uukanshu` command and its
  dependencies via [`uv`](https://docs.astral.sh/uv/), on any platform
- 🚢 **Standalone binaries** — single-file executables (no Python needed) for
  Linux, macOS, and Windows from the
  [Releases](https://github.com/<you>/uukanshu/releases) page
- 🌍 **Cross-platform** — no external fetch binaries; anything that runs Python can run `uukanshu`

---

## Requirements

| Dependency                           | Why                                                           | Notes                                   |
| ------------------------------------ | ------------------------------------------------------------- | --------------------------------------- |
| **Python ≥ 3.10**                    | Runs the app (source installs only)                           | Fetching uses only the standard library |
| **[uv](https://docs.astral.sh/uv/)** | Installs the CLI and manages dependencies (`uv tool install`) | Must be on `PATH`                       |

> **No Python? No problem.** Prebuilt single-file binaries are available on
> the [Releases](https://github.com/<you>/uukanshu/releases) page — see
> [Getting Started](#getting-started).

## Getting Started

Two ways in: download a **prebuilt binary** (nothing to install), or install
the CLI with **uv**.

### Option A — prebuilt binary (no Python needed)

1. Download the file for your platform from the
   [Releases](https://github.com/<you>/uukanshu/releases) page:
   `uukanshu-linux-x86_64`, `uukanshu-macos-arm64`, or
   `uukanshu-windows-x86_64.exe`.
2. Make it executable and put it on your `PATH` (Linux/macOS):

   ```sh
   mv uukanshu-linux-x86_64 ~/.local/bin/uukanshu
   chmod +x ~/.local/bin/uukanshu
   ```

   On Windows, just place `uukanshu-windows-x86_64.exe` somewhere on `PATH`.

3. The binaries are not code-signed, so expect a one-time OS prompt:

   - **macOS Gatekeeper:** `xattr -d com.apple.quarantine uukanshu`, or
     right-click the binary → _Open_ on first launch
   - **Windows SmartScreen:** _More info_ → _Run anyway_

### Option B — install with uv

### 1. Install uv

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See the [uv docs](https://docs.astral.sh/uv/getting-started/installation/) for
other platforms (Windows:
`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`).

### 2. Install uukanshu

From a local clone:

```sh
git clone https://github.com/<you>/uukanshu && cd uukanshu
uv tool install .
```

…or straight from git, without cloning:

```sh
uv tool install git+https://github.com/<you>/uukanshu
```

`uv` places a `uukanshu` command on your `PATH` (run `uv tool update-shell`
once if your shell can't find it).

### Read something

```sh
# Browse a book's chapter list, then pick one by number
uukanshu --book <ID> --list
uukanshu --book <ID> --chapter 6

# Or jump straight to a chapter by URL
uukanshu https://uukanshu.cc/book/<ID>/<CHAPTER>.html
```

**Finding a book ID:** the ID is the number in `/book/<ID>/` URLs. Browse
the library (e.g. <https://uukanshu.cc/class_1_1.html>) or search by title:

```txt
https://uukanshu.cc/modules/article/search.php?q=<title>
```

---

## Usage

```txt
uukanshu [URL] [options]
```

| Option               | Description                                                                      |
| -------------------- | -------------------------------------------------------------------------------- |
| `URL`                | Chapter URL to open directly                                                     |
| `-b`, `--book <ID>`  | Book ID (the number from `/book/<ID>/` URLs)                                     |
| `-c`, `--chapter N`  | Chapter number from the book's TOC (default: 1)                                  |
| `-l`, `--list`       | List the book's chapters as plain text and exit                                  |
| `-z`, `--simplified` | Convert Traditional → Simplified Chinese                                         |
| `--pad N`            | Padding around the text: N blank rows top/bottom, N cols left/right (default: 2) |
| `-t`, `--theme NAME` | Reader color theme (default: `night`)                                            |
| `-p`, `--print`      | Print clean text to stdout instead of opening the reader                         |

### Examples

```sh
# Simplified Chinese
uukanshu --book <ID> -z

# Roomier margins
uukanshu https://uukanshu.cc/book/<ID>/<CHAPTER>.html --pad 4

# Start in the sepia theme
uukanshu --book <ID> --theme sepia

# Save a chapter as clean text
uukanshu --book <ID> --chapter 6 -z --print > chapter6.txt
```

---

## Reader Keybindings

All keys are also shown in the footer bar while reading.

| Key                                                                                      | Action                                                                                                                                  |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| <kbd>n</kbd> / <kbd>p</kbd>                                                              | Next / previous chapter                                                                                                                 |
| <kbd>l</kbd>                                                                             | Chapter list — opens instantly with a spinner while the list is fetched; <kbd>Enter</kbd> jumps, <kbd>Esc</kbd> or <kbd>q</kbd> closes  |
| <kbd>d</kbd> / <kbd>u</kbd>                                                              | Half-page down / up (smooth glide)                                                                                                      |
| <kbd>↑</kbd> <kbd>↓</kbd> <kbd>PgUp</kbd> <kbd>PgDn</kbd> <kbd>Home</kbd> <kbd>End</kbd> | Standard scrolling                                                                                                                      |
| <kbd>z</kbd>                                                                             | Toggle Simplified / Traditional — instantly re-renders the chapter text, header title, chapter list, and UI messages without refetching |
| <kbd>t</kbd> / <kbd>T</kbd>                                                              | Cycle color themes forward / backward                                                                                                   |
| <kbd>q</kbd>                                                                             | Quit                                                                                                                                    |

---

## Themes

Cycle in-app with <kbd>t</kbd>, or set one at launch with `--theme`:

`night` (default) · `sepia` · `paper` · `catppuccin-frappe` · `catppuccin-macchiato` · `catppuccin-mocha` · `tokyo-night` · `matrix`

---

## Environment Variables

| Variable                | Effect                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `COLORTERM=truecolor`   | Enable 24-bit truecolor so themes render with their exact hex colors (see note below) |
| `UUKANSHU_SIMPLIFIED=1` | Start with Simplified Chinese enabled (same as `-z`)                                  |
| `UUKANSHU_PAD=N`        | Default text padding (same as `--pad N`)                                              |
| `UUKANSHU_THEME=NAME`   | Default color theme (same as `--theme NAME`)                                          |

Example:

```sh
export UUKANSHU_SIMPLIFIED=1
export UUKANSHU_PAD=6            # roomier margins by default
export UUKANSHU_THEME=sepia
```

### Truecolor note

The built-in themes are defined with exact hex colors. Most modern terminal
emulators (iTerm2, Windows Terminal, kitty, Alacritty, GNOME Terminal, etc.)
report truecolor support automatically, but if colors look washed out or
bands of them seem approximated, your terminal may not be advertising it.
Force 24-bit color with:

```sh
export COLORTERM=truecolor
```

Without it, Textual falls back to the 256-color palette and approximates
the theme colors — most visible on subtle themes like `sepia` and `paper`.

---

## Updating & Uninstalling

```sh
uv tool upgrade uukanshu      # after pulling new commits / a new release
uv tool uninstall uukanshu
```

To build a binary yourself (any platform, on that platform):

```sh
uv run --with pyinstaller --with . pyinstaller uukanshu.spec --noconfirm
# → dist/uukanshu (dist/uukanshu.exe on Windows)
```

---

## Troubleshooting

**"failed to fetch …"** — transient network errors are retried automatically,
but if it keeps failing, check your connection (or whether uukanshu.cc is
up). If you see **"blocked by Cloudflare"**, try again later or from a
different network.

**`uukanshu: command not found`** — run `uv tool update-shell`, then restart
your shell (or add `$(uv tool dir --bin)` to `PATH` yourself).

**`error: give a chapter URL or --book <id>`** — you need to pass either a
chapter URL or `--book <ID>`. Run `uukanshu --help` for all options.

**Chapter content not found** — make sure the URL points to a chapter
(`/book/<ID>/<CHAPTER>.html`), not the book's index page.
