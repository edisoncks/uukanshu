# uukanshu

Read novels from [uukanshu.cc](https://uukanshu.cc) right in your terminal —
just the story: no ads, no clutter, no pop-ups.

- 📖 A clean, comfortable reading view that reflows as you resize the window
- 🧭 Jump between chapters, or browse the full chapter list
- 🀄 Optional conversion of Traditional → Simplified Chinese, on the fly
- 🎨 8 color themes (night, sepia, paper, Catppuccin, Tokyo Night, Matrix)

---

## Quick Start

### 1. Download

Grab one file from the
[Releases page](https://github.com/edisoncks/uukanshu-cli/releases/latest) —
no installation needed:

Download the file for your computer and **rename it** as shown — this makes
every command below shorter:

| Your computer           | Download this asset           | Rename it to   |
| ----------------------- | ----------------------------- | -------------- |
| Mac (M1 / M2 / M3 / M4) | `uukanshu-macos-arm64`        | `uukanshu`     |
| Windows 64-bit          | `uukanshu-windows-x86_64.exe` | `uukanshu.exe` |
| Linux 64-bit            | `uukanshu-linux-x86_64`       | `uukanshu`     |

### 2. Run it

#### Windows

1. Open **PowerShell** (press Start, type "PowerShell", press Enter).
2. Go to your Downloads folder:

   ```powershell
   cd $env:USERPROFILE\Downloads
   ```

3. Start reading (paste any chapter's or book's web address after the
   program name):

   ```powershell
   .\uukanshu.exe https://uukanshu.cc/book/18957/
   ```

4. The first time, Windows shows **"Windows protected your PC"** — click
   **More info → Run anyway**. This appears only because the app isn't
   code-signed; it happens once.

#### Mac (Apple Silicon)

1. Open **Terminal** (press ⌘-Space, type "Terminal", press Enter).
2. Go to your Downloads folder and allow the file to run:

   ```sh
   cd ~/Downloads
   chmod +x uukanshu
   ```

3. Start reading:

   ```sh
   ./uukanshu https://uukanshu.cc/book/18957/
   ```

4. If macOS refuses to open it ("cannot verify the developer"): open
   **System Settings → Privacy & Security**, scroll to **Security**, and
   click **Open Anyway**. This is needed once.

#### Linux

1. Open a terminal.
2. Go to your Downloads folder and allow the file to run:

   ```sh
   cd ~/Downloads
   chmod +x uukanshu
   ```

3. Start reading:

   ```sh
   ./uukanshu https://uukanshu.cc/book/18957/
   ```

### 3. Pick something to read

The easiest way: open [uukanshu.cc](https://uukanshu.cc) in your browser,
find a book you like, copy its **book address** from the address bar (it
looks like `https://uukanshu.cc/book/18957/`), and paste it after the
program name — reading starts at chapter 1:

```sh
./uukanshu https://uukanshu.cc/book/18957/                          # Mac / Linux
.\uukanshu.exe https://uukanshu.cc/book/18957/                      # Windows
```

You can also paste a **chapter's** web address to jump straight there, or
use the **book ID** — the number in the book's address (here `18957`):

```sh
uukanshu --book 18957                    # open chapter 1
uukanshu --book 18957 --chapter 6        # open chapter 6
uukanshu --book 18957 --list             # just show all chapter titles
uukanshu https://uukanshu.cc/book/18957/ --chapter 6   # same, via URL
```

You can browse the whole library at <https://uukanshu.cc/class_1_1.html> or
search by title: `https://uukanshu.cc/modules/article/search.php?q=<title>`.

---

## While reading

| Key                             | What it does                                                 |
| ------------------------------- | ------------------------------------------------------------ |
| <kbd>n</kbd> / <kbd>p</kbd>     | Next / previous chapter                                      |
| <kbd>l</kbd>                    | Chapter list — <kbd>Enter</kbd> jumps, <kbd>Esc</kbd> closes |
| <kbd>d</kbd> / <kbd>u</kbd>     | Half a page down / up                                        |
| Arrow keys, PgUp/PgDn, Home/End | Scroll                                                       |
| <kbd>z</kbd>                    | Switch between Traditional and Simplified Chinese            |
| <kbd>t</kbd> / <kbd>T</kbd>     | Change the color theme                                       |
| <kbd>q</kbd>                    | Quit                                                         |

---

## Options

```txt
uukanshu [chapter URL] [options]
```

| Option               | What it does                                                               |
| -------------------- | -------------------------------------------------------------------------- |
| `URL`                | Chapter web address to open, **or** a book's address to start at chapter 1 |
| `-b`, `--book <ID>`  | Open a book by its ID (default: chapter 1)                                 |
| `-c`, `--chapter N`  | Which chapter to open (default: 1)                                         |
| `-l`, `--list`       | Show the chapter titles and exit                                           |
| `-z`, `--simplified` | Show Simplified Chinese instead of Traditional                             |
| `--pad N`            | Roomier margins (default: 2)                                               |
| `-t`, `--theme NAME` | Start with a color theme (default: `night`)                                |
| `-p`, `--print`      | Print the chapter as plain text instead of opening the reader              |
| `--no-update-check`  | Disable the new-version reminder                                           |
| `--version`          | Show the version and exit                                                  |

Every option can also be defaulted through an environment variable, so you
don't have to retype flags each time:

| Environment variable       | Effect                                             |
| ------------------------------ | -------------------------------------------------- |
| `UUKANSHU_SIMPLIFIED`          | Set to `1` to start in Simplified Chinese          |
| `UUKANSHU_PAD`                 | Default margin size (same as `--pad N`)            |
| `UUKANSHU_THEME`               | Default color theme (same as `--theme NAME`)       |
| `UUKANSHU_NO_UPDATE_CHECK`     | Set to `1` to disable the new-version reminder     |

`--chapter` only applies when starting from a book address or `--book <ID>`;
a chapter web address already names its chapter, and combining the two is
rejected with an error.

**Themes:** `night` · `sepia` · `paper` · `catppuccin-frappe` ·
`catppuccin-macchiato` · `catppuccin-mocha` · `tokyo-night` · `matrix`

Save a chapter as a text file:

```powershell
.\uukanshu.exe --book 18957 --chapter 6 -z --print > chapter6.txt
```

---

## Troubleshooting

**"Windows protected your PC" / macOS "cannot verify the developer"** — the
binaries are not code-signed. On Windows: **More info → Run anyway**. On Mac:
**System Settings → Privacy & Security → Open Anyway**, or run
`xattr -d com.apple.quarantine <file>` in Terminal. Each happens once.

**"failed to fetch …"** — short network hiccups are retried automatically.
If it keeps failing, check your connection or try again later. If you see
**"blocked by Cloudflare"**, try again later or from a different network.

**"error: give a chapter URL or --book <id>"** — you need to tell uukanshu
what to read: paste a chapter's web address, or use `--book <ID>`.

**"could not find chapter content"** — the web address must point to a
**chapter** (`…/book/<ID>/<CHAPTER>.html`), not the book's index page.
Pressing <kbd>p</kbd> on a book's first chapter or <kbd>n</kbd> on its last
one is safe: the reader says "start of book" / "end of book" instead.

**Colors look washed out** — your terminal may not be using full color. Try
setting `COLORTERM=truecolor` before starting (PowerShell:
`$env:COLORTERM="truecolor"`).

---

## Updating

The reader checks the GitHub Releases page on startup (at most once
every 12 hours) and shows a short notice when a newer version is
available. To turn the reminder off: pass `--no-update-check` or set
`UUKANSHU_NO_UPDATE_CHECK=1`.

To update, download the newest file from the
 [Releases page](https://github.com/edisoncks/uukanshu-cli/releases/latest) and
 replace your old one. Your settings aren't stored anywhere, so nothing else
 to do.

---

## For developers

Developers can also run uukanshu straight from Python source with
[`uv`](https://docs.astral.sh/uv/) (`uv tool install .` — no binary
involved), build the binaries, and cut releases. See
[DEVELOPING.md](DEVELOPING.md).
