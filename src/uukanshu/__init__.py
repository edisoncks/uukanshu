"""uukanshu — read novels from uukanshu.cc in your terminal.

Fetches chapters over plain HTTPS using only the Python standard library,
strips the page down to just the chapter text, optionally converts
Traditional -> Simplified Chinese (OpenCC), and shows it in a Textual
reading pane: CJK-aware reflowing padding, live resize, and in-app
chapter navigation.

WHAT YOU NEED
  * Nothing but Python 3.10+ — fetching uses only the standard library;
    OpenCC + textual are installed with the package (and are bundled into
    the standalone release binaries).


KEYS (shown in the footer bar too)
  n           next chapter          p   previous chapter
  l           chapter list — opens instantly with a spinner while the list
              is fetched; cached per book. Esc or q closes it, Enter jumps
  q           quit
  d/u            half-page down/up (smooth glide)   arrows / PgUp / PgDn / Home / End
  z           toggle Simplified / Traditional — instantly re-renders the
              chapter text, header title, chapter list, and UI messages
              without refetching
  t/T         color theme — cycle night → sepia → paper →
              catppuccin-frappe → catppuccin-macchiato → catppuccin-mocha →
              tokyo-night → matrix (T goes in reverse)

  Built-in messages follow the content's mode; -z starts in Simplified.

EXAMPLES
  # browse a book's chapter list, then pick one by number
  uukanshu --book <ID> --list
  uukanshu --book <ID> --chapter 6

  # start a book from its address (opens chapter 1)
  uukanshu https://uukanshu.cc/book/<ID>/

  # read a specific chapter straight from its URL
  uukanshu https://uukanshu.cc/book/<ID>/<CHAPTER>.html

  # Simplified Chinese, custom text padding (default: 2 cols / 1 blank line)
  uukanshu --book <ID> -z
  uukanshu https://uukanshu.cc/book/<ID>/<CHAPTER>.html --pad 4
  export UUKANSHU_SIMPLIFIED=1     # -z by default
  export UUKANSHU_PAD=6            # roomier margins by default

  # color themes: night (default) | sepia | paper | catppuccin-frappe |
  # catppuccin-macchiato | catppuccin-mocha | tokyo-night | matrix,
  # or cycle with t
  uukanshu --book <ID> --theme sepia
  export UUKANSHU_THEME=sepia      # theme by default

  # dump clean text to stdout instead of launching the reader
  uukanshu --book <ID> --chapter 6 -z --print > chapter6.txt

TIPS
  * Textual reflows the text as you resize the terminal — padding stays
    correct on all four sides. No fixed-width wrapping, so the old less
    hacks are gone entirely.
  * Fetching is plain HTTPS with browser-like headers; transient network
    failures are retried automatically. If you still see errors, check
    your connection (or whether the site is up).
  * Book IDs are the number in /book/<ID>/ URLs. Find them by browsing the
    library (https://uukanshu.cc/class_1_1.html etc.) or searching by title:
    https://uukanshu.cc/modules/article/search.php?q=<title>
"""

__version__ = "0.1.3"

import argparse
import asyncio
import gzip
import html
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Footer, Header, LoadingIndicator, OptionList, Static
from textual.widgets.option_list import Option
from rich.text import Text

BASE = "https://uukanshu.cc"

# ----------------------------------------------------------------- themes

# Reading-oriented color themes; `night` is the default (most terminals
# run dark, and Textual offers no light/dark detection to auto-pick).
READER_THEMES = [
    Theme(
        name="night",
        dark=True,
        primary="#7d9ac1", secondary="#9a8ec1", accent="#c19a7d",
        foreground="#c9cfd8", background="#12161d",
        surface="#181d26", panel="#1a2029",
        warning="#d8b26a", error="#c96f6f", success="#79b28a",
    ),
    Theme(
        name="sepia",
        dark=False,
        primary="#8a5a2b", secondary="#6b6136", accent="#a0672f",
        foreground="#3b2f22", background="#f4ecd8",
        surface="#ede1c4", panel="#e7d9b8",
        warning="#a3722a", error="#a03d3d", success="#5d7d46",
    ),
    Theme(
        name="paper",
        dark=False,
        primary="#3a6ea5", secondary="#5a7d5a", accent="#8a6d3b",
        foreground="#22262b", background="#fbfbf9",
        surface="#f1f1ee", panel="#e9e9e4",
        warning="#a3722a", error="#a03d3d", success="#4a7d4a",
    ),
    Theme(
        name="catppuccin-frappe",
        dark=True,
        primary="#ca9ee6", secondary="#8caaee", accent="#ef9f76",
        foreground="#c6d0f5", background="#303446",
        surface="#414559", panel="#292c3c",
        warning="#e5c890", error="#e78284", success="#a6d189",
    ),
    Theme(
        name="catppuccin-macchiato",
        dark=True,
        primary="#c6a0f6", secondary="#8aadf4", accent="#f5a97f",
        foreground="#cad3f5", background="#24273a",
        surface="#363a4f", panel="#1e2030",
        warning="#eed49f", error="#ed8796", success="#a6da95",
    ),
    Theme(
        name="catppuccin-mocha",
        dark=True,
        primary="#cba6f7", secondary="#89b4fa", accent="#fab387",
        foreground="#cdd6f4", background="#1e1e2e",
        surface="#313244", panel="#181825",
        warning="#f9e2af", error="#f38ba8", success="#a6e3a1",
    ),
    Theme(
        name="tokyo-night",
        dark=True,
        primary="#7aa2f7", secondary="#bb9af7", accent="#ff9e64",
        foreground="#c0caf5", background="#1a1b26",
        surface="#292e42", panel="#16161e",
        warning="#e0af68", error="#f7768e", success="#9ece6a",
    ),
    Theme(
        name="matrix",
        dark=True,
        primary="#33ff66", secondary="#1f9d4d", accent="#9d1f6e",
        foreground="#33ff66", background="#000000",
        surface="#04140a", panel="#071a0e",
        warning="#33ffcc", error="#ff3366", success="#33ff66",
    ),
]

# ---------------------------------------------------------------- fetching

# uukanshu.cc serves plain HTML to ordinary HTTPS clients; a browser-like
# header set is all it takes (no Cloudflare challenge, no headless browser).
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Frozen binaries (PyInstaller) don't see the system CA store reliably;
# prefer certifi's bundled roots, fall back to the system default.
try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()


def fetch(url: str) -> str:
    """Fetch a uukanshu page over plain HTTPS and return its HTML."""
    page = None
    last_exc = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30,
                                        context=_SSL_CONTEXT) as r:
                body = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            page = body.decode("utf-8", errors="replace")
            break
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    if page is None:
        raise RuntimeError(f"failed to fetch {url}: {last_exc}")
    if ("Attention Required" in page or "Just a moment" in page
            or "you have been blocked" in page):
        raise RuntimeError(
            "blocked by Cloudflare — try again later or from a "
            "different network")
    return page


def absolutize(href: str) -> str:
    return href if href.startswith("http") else BASE + href


def link(page: str, label: str):
    m = re.search(rf'<a href="([^"]+)"[^>]*>\s*{label}\s*</a>', page)
    return m and absolutize(m.group(1))


def chapter_list(toc_page: str, book_id: str | None = None):
    """Return [(position, chapter_page_id, title, url)] for a book TOC page.

    The TOC page leads with a 'latest updates' block whose chapters also
    appear in the full ordered list below. Keeping the LAST occurrence of
    each (book, chapter) pair positions chapters in reading order.

    book_id, when given, drops chapter links that point at a different
    book (recommendation blocks etc.); None accepts every book. Chapter
    hrefs may be site-relative or absolute.
    """
    matches = list(re.finditer(
        r'href="(?:' + re.escape(BASE) + r')?(/book/(\d+)/(\d+)\.html)"'
        r'[^>]*>\s*([^<]+?)\s*</a>',
        toc_page))
    last_idx = {}
    for i, m in enumerate(matches):
        if book_id is not None and m.group(2) != str(book_id):
            continue
        last_idx[(m.group(2), m.group(3))] = i
    out, seen = [], set()
    for i, m in enumerate(matches):
        if book_id is not None and m.group(2) != str(book_id):
            continue
        key = (m.group(2), m.group(3))
        if key in seen or last_idx[key] != i:
            continue
        seen.add(key)
        out.append((len(out) + 1, int(m.group(3)), m.group(4).strip(),
                    BASE + m.group(1)))
    return out


def extract_chapter(page: str, url: str):
    """Pull book name, chapter title, clean text, and nav links from a page."""
    t = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    title = re.sub(r"<[^>]+>", "", t.group(1)).strip() if t else url

    bc = re.findall(r'<a href="(?:https?://[^"]*)?/book/\d+/"[^>]*>([^<]+)</a>',
                    page)
    book = bc[-1].strip() if bc else ""

    m = re.search(r'<div class="readcotent[^"]*"[^>]*>(.*)', page, re.S)
    if not m:
        raise RuntimeError("could not find chapter content on the page "
                           "(is this a chapter URL?)")
    body = m.group(1)
    # Cut at the nav-row container: from the "上一章 / 章节目录 / 下一章"
    # box to the end of the page it's all UI/footer noise — the keyboard
    # tip, the copyright blurb, the "Copyright ... TOP↑" footer, and the
    # GTM iframe/noscript leftovers — never chapter text.
    body = re.split(r'<div class="mulu-box"', body, maxsplit=1)[0]
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = body.replace("&emsp;", "")
    lines = [l.strip() for l in html.unescape(body).splitlines() if l.strip()]
    text = "\n\n".join(lines)
    # Belt-and-braces for pages without the mulu-box container: also cut at
    # the literal nav row, tolerating the "章节/章節" prefix (simplified /
    # traditional) that prefixes the link label.
    text = re.split(r"\n*上一章\s+(?:章节|章節)?目[录錄]\s+下一章", text)[0].rstrip()

    return (book, title, text,
            link(page, "上一章"), link(page, "目[录錄]") or link(page, "目录"),
            link(page, "下一章"))


# OpenCC's t2s is deliberately conservative: it correctly preserves 著
# in real words (著名, 著作, 显著...) but also leaves the Traditional
# aspect particle 著 (看著 -> 看着) unconverted. Convert ONLY the particle
# by scanning past the protected words — a blanket 著->着 replace would
# turn 著名 into 着名. Simplified forms; this runs after cc.convert().
# Extend the list as misses are found.
_ZHU_KEEP = ("著书立说", "著名", "著作", "著称", "著述", "著者", "著录",
             "著书", "昭著", "显著", "卓著", "原著", "名著", "巨著",
             "专著", "编著", "译著", "论著", "合著", "新著", "旧著",
             "遗著", "拙著", "大著")


def _fix_particle_zhu(s: str) -> str:
    """著 -> 着 for the aspect particle only, never inside _ZHU_KEEP."""
    out, i, n = [], 0, len(s)
    while i < n:
        for w in _ZHU_KEEP:
            if s.startswith(w, i):
                out.append(w)
                i += len(w)
                break
        else:
            out.append("着" if s[i] == "著" else s[i])
            i += 1
    return "".join(out)


def to_simplified(cc, *strs):
    return [_fix_particle_zhu(cc.convert(s)) for s in strs]


# ---------------------------------------------------------------- reader UI

class TocOptionList(OptionList):
    """Chapter picker list that opens scrolled to the current chapter.

    OptionList.on_show() scrolls minimally so the highlighted option just
    becomes visible (bottom of the viewport for a deep chapter); here we
    pin the current chapter at the top instead, so browsing starts from
    where you are.
    """

    def on_show(self) -> None:
        self.scroll_to_highlight(top=True)


class TocScreen(ModalScreen):
    """Modal chapter picker: arrows to browse, Enter to jump, Esc to close."""

    CSS = """
    TocScreen { align: center middle; }
    #tocbox { width: 80%; height: 90%; border: round $primary;
              background: $surface; padding: 1 2; }
    #tochead { height: auto; margin-bottom: 1; text-style: bold; }
    LoadingIndicator { height: auto; }
    OptionList { height: 1fr; }
    """
    BINDINGS = [
        Binding("escape", "close", "close", priority=True),
        Binding("q", "close", "close"),
        Binding("d", "half(1)", "down", priority=True),
        Binding("u", "half(-1)", "up", priority=True),
    ]

    def __init__(self, current_url, ui=None):
        super().__init__()
        self.chapters = []
        self.current_url = current_url
        self.ui = ui or (lambda s: s)

    def compose(self) -> ComposeResult:
        with Vertical(id="tocbox"):
            yield Static(self.ui("章节目录 / Chapters — ↑↓/d/u · Enter jump · Esc close"),
                         id="tochead")
            yield LoadingIndicator(id="tocspin")
            yield TocOptionList()

    def on_mount(self) -> None:
        self.query_one(OptionList).can_focus = True
        if self.chapters:
            self._fill(self.chapters)

    def action_half(self, sign: int) -> None:
        """Half-page step that moves the selection with the view, so d/u,
        arrow keys, and Enter all agree on which chapter is selected."""
        ol = self.query_one(OptionList)
        if not ol.option_count:
            return
        step = max(1, ol.container_size.height // 2) * sign
        current = ol.highlighted if ol.highlighted is not None else 0
        # watch_highlighted scrolls the selection into view automatically.
        ol.highlighted = min(max(current + step, 0), ol.option_count - 1)

    def populate(self, chapters) -> None:
        """Safe to call before OR after the modal has mounted."""
        self.chapters = chapters
        if self.is_mounted:
            self._fill(chapters)

    def _fill(self, chapters) -> None:
        self.query_one("#tocspin", LoadingIndicator).display = False
        ol = self.query_one(OptionList)
        ol.clear_options()
        ol.add_options(
            Option(f"{pos:>5}  {title}", id=str(pos))
            for pos, _id, title, _url in chapters)
        for pos, _id, _t, url in chapters:
            if url == self.current_url:
                ol.highlighted = pos - 1
                ol.scroll_to_highlight(top=True)
                break
        ol.focus()

    def show_error(self, msg: str) -> None:
        if not self.is_mounted:
            return
        self.query_one("#tocspin", LoadingIndicator).display = False
        self.query_one("#tochead", Static).update(
            f"[bold red]error:[/] {msg} — Esc/q to close")

    def on_option_list_option_selected(self, event) -> None:
        pos = int(str(event.option_id))
        url = next((u for p, _i, _t, u in self.chapters if p == pos), None)
        self.dismiss(url)

    def action_close(self) -> None:
        self.dismiss(None)


class Reader(App):
    TITLE = "uukanshu"
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #page { height: 1fr; }
    #doc { width: 1fr; }
    """

    BINDINGS = [
        Binding("d", "half(1)", "down"),
        Binding("u", "half(-1)", "up"),
        Binding("n", "next", "next"),
        Binding("p", "prev", "prev"),
        Binding("l", "list", "chapters"),
        Binding("z", "toggle_simplified", "simplified"),
        Binding("t", "cycle_theme", "theme", key_display="t/T"),
        Binding("T", "cycle_theme_reverse", show=False),
        Binding("q", "quit", "quit"),
    ]

    def __init__(self, url: str, cc, pad: int, theme: str = "night"):
        super().__init__()
        for t in READER_THEMES:
            self.register_theme(t)
        self.theme = theme
        self.url = url
        self.pad = pad
        self.simplified = cc is not None
        self._t2s = cc    # t2s converter (reused from CLI when -z; built lazily otherwise)
        self._s2t = None  # lazily built: chrome localization for Traditional mode
        self._raw = None  # raw (book, title, text) of the last fetched chapter
        self.next_url = self.prev_url = None
        m = re.search(r"/book/(\d+)/", url)
        self.book_id = m.group(1) if m else None
        self.chapters_cache = None
        self._cache_book = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield VerticalScroll(Static("", id="doc"), id="page")
        yield Footer()

    def on_mount(self) -> None:
        doc = self.query_one("#doc", Static)
        doc.styles.padding = (self.pad, self.pad)
        self.load_chapter(self.url)

    def _conv_t2s(self):
        """Lazily built Traditional -> Simplified converter."""
        if self._t2s is None:
            import opencc
            self._t2s = opencc.OpenCC("t2s")
        return self._t2s

    def ui(self, s: str) -> str:
        """Built-in chrome strings are written Simplified; show them
        Traditional while the reader is in Traditional mode."""
        if self.simplified:
            return s
        if self._s2t is None:
            try:
                import opencc
                self._s2t = opencc.OpenCC("s2t")
            except Exception:
                self._s2t = False
        return self._s2t.convert(s) if self._s2t else s

    def _render(self, book, title, text):
        """Render the given (raw) chapter content in the current mode."""
        if self.simplified:
            book, title, text = to_simplified(self._conv_t2s(), book, title, text)
        self.title = f"{book} — {title}" if book else title
        self.query_one("#doc", Static).update(Text.assemble(
            (book + "\n", "bold"),
            (title + "\n\n", "bold cyan"),
            (text + "\n", ""),
        ))

    def action_half(self, sign: int) -> None:
        page = self.query_one("#page", VerticalScroll)
        step = max(1, page.container_size.height // 2) * sign
        page.scroll_relative(0, step, speed=40, easing="out_quart")

    # -- content loading

    @work(exclusive=True, group="nav")
    async def load_chapter(self, url: str) -> None:
        doc = self.query_one("#doc", Static)
        doc.update(self.ui("载入中… loading…"))
        try:
            page = await asyncio.to_thread(fetch, url)
            book, title, text, prev_url, _toc, next_url = extract_chapter(page, url)
        except Exception as exc:
            doc.update(f"[bold red]error:[/] {exc}")
            return
        m = re.search(r"/book/(\d+)/", url)
        if m:
            self.book_id = m.group(1)
        self.url = url
        self.prev_url, self.next_url = prev_url, next_url
        self._raw = (book, title, text)
        self._render(book, title, text)
        self.query_one(VerticalScroll).scroll_home(immediate=True)

    # -- navigation actions

    @property
    def modal(self) -> bool:
        return isinstance(self.screen, TocScreen)

    def action_next(self) -> None:
        if self.modal:
            return
        if self.next_url:
            self.load_chapter(self.next_url)
        else:
            self.notify(self.ui("已是最新一章") + " / end of book", severity="warning")

    def action_prev(self) -> None:
        if self.modal:
            return
        if self.prev_url:
            self.load_chapter(self.prev_url)
        else:
            self.notify(self.ui("已是第一章") + " / start of book", severity="warning")

    def action_toggle_simplified(self) -> None:
        if self._raw is None:
            self.notify(self.ui("尚无内容") + " / nothing loaded yet",
                        severity="warning")
            return
        self.simplified = not self.simplified
        self._render(*self._raw)
        if (self.chapters_cache and self._cache_book == self.book_id
                and isinstance(self.screen, TocScreen)):
            self.screen.populate(self._toc_converted(self.chapters_cache))
            self.screen.query_one("#tochead", Static).update(
                self.ui("章节目录 / Chapters — ↑↓/d/u · Enter jump · Esc close"))

    def _cycle_theme(self, step: int) -> None:
        names = [t.name for t in READER_THEMES]
        self.theme = names[(names.index(self.theme) + step) % len(names)]
        self.notify(self.ui("主题") + f" / theme: {self.theme}")

    def action_cycle_theme(self) -> None:
        self._cycle_theme(1)

    def action_cycle_theme_reverse(self) -> None:
        self._cycle_theme(-1)

    def _toc_converted(self, chapters):
        """Chapter list with titles converted to the current mode. The
        cache itself stays raw — OpenCC round-trips aren't lossless."""
        if not self.simplified:
            return chapters
        conv = to_simplified(self._conv_t2s(), *[t for _p, _i, t, _u in chapters])
        return [(p, i, t2, u) for (p, i, _t, u), t2 in zip(chapters, conv)]

    def action_list(self) -> None:
        if self.modal:
            return
        if not self.book_id:
            self.notify(self.ui("无法确定书籍ID") + " / unknown book id",
                        severity="error")
            return
        screen = TocScreen(self.url, ui=self.ui)
        self.push_screen(screen, self.on_toc_choice)
        if self.chapters_cache and self._cache_book == self.book_id:
            screen.populate(self._toc_converted(self.chapters_cache))
        else:
            self.fetch_toc(screen)

    @work(exclusive=True, group="toc")
    async def fetch_toc(self, screen: TocScreen) -> None:
        """Fill an already-visible TOC modal once its book page has loaded."""
        book_id = self.book_id
        try:
            page = await asyncio.to_thread(fetch, f"{BASE}/book/{book_id}/")
            chapters = chapter_list(page, book_id)  # cached raw; converted at populate time
        except Exception as exc:
            if self.screen is screen:
                screen.show_error(str(exc))
            return
        self.chapters_cache, self._cache_book = chapters, book_id
        if self.screen is screen:
            screen.populate(self._toc_converted(chapters))

    def on_toc_choice(self, url) -> None:
        if url:
            self.url = url
            self.load_chapter(url)


# ---------------------------------------------------------------- CLI

def book_url_from_arg(url: str):
    """Return the book index URL if `url` is one (e.g. .../book/123/ or
    .../book/123/index.html), else None. Chapter URLs never match."""
    m = re.fullmatch(rf"{BASE}/book/(\d+)/?(?:index\.html)?", url or "")
    return f"{BASE}/book/{m.group(1)}/" if m else None


def resolve_start_url(args):
    book_url = book_url_from_arg(args.url)
    if book_url:
        book_id = re.search(r"/book/(\d+)/", book_url).group(1)
        chapters = chapter_list(fetch(book_url), book_id)
        if not chapters:
            sys.exit(f"error: no chapters found at {book_url}.")
        idx = max(1, min(args.chapter, len(chapters)))
        return chapters[idx - 1][3]
    if args.url:
        return args.url
    if not args.book:
        sys.exit("error: give a chapter URL or --book <id> (see --help).")
    page = fetch(f"{BASE}/book/{args.book}/")
    chapters = chapter_list(page, args.book)
    if not chapters:
        sys.exit("error: no chapters found on the book page.")
    idx = max(1, min(args.chapter, len(chapters)))
    return chapters[idx - 1][3]


def _force_utf8_stdio():
    """Windows consoles default to a legacy codepage (e.g. cp1252) that
    cannot encode the help text (→, CJK) or novel content; force UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and stream.encoding.lower() not in (
                    "utf-8", "utf8"):
                stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


def main():
    _force_utf8_stdio()
    try:
        run()
    except (RuntimeError, OSError) as exc:
        sys.exit(f"error: {exc}")


def run():
    ap = argparse.ArgumentParser(
        prog="uukanshu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__.strip(),
    )
    ap.add_argument("--version", action="version",
                    version=f"uukanshu {__version__}")
    ap.add_argument("url", nargs="?", help="chapter or book URL to start at")
    ap.add_argument("--book", "-b", help="book ID, from /book/<ID>/ URLs")
    ap.add_argument("--chapter", "-c", type=int, default=1, metavar="N",
                    help="chapter number from the book TOC (default: 1)")
    ap.add_argument("--list", "-l", action="store_true",
                    help="list chapters of --book (plain text) and exit")
    ap.add_argument("--simplified", "-z", action="store_true",
                    default=os.environ.get("UUKANSHU_SIMPLIFIED") == "1",
                    help="convert Traditional -> Simplified Chinese "
                         "(env UUKANSHU_SIMPLIFIED=1 to default on)")
    ap.add_argument("--pad", type=int,
                    default=int(os.environ.get("UUKANSHU_PAD", "2")),
                    metavar="N",
                    help="padding around text in the reader: N blank rows top/"
                         "bottom, N cols left/right (default 2; env "
                         "UUKANSHU_PAD=N)")
    ap.add_argument("--theme", "-t", choices=[t.name for t in READER_THEMES],
                    default=os.environ.get("UUKANSHU_THEME", "night"),
                    metavar="NAME",
                    help="reader color theme (default: night; env "
                         "UUKANSHU_THEME=NAME); cycle in-app with t")
    ap.add_argument("--print", "-p", action="store_true", dest="plain",
                    help="print plain text to stdout, no reader UI")
    args = ap.parse_args()

    cc = None
    if args.simplified:
        import opencc
        cc = opencc.OpenCC("t2s")

    if args.list:
        book_url = book_url_from_arg(args.url)
        if not book_url and not args.book:
            sys.exit("error: --list needs a book URL or --book <id>.")
        if book_url:
            toc_url, book_id = (book_url,
                                re.search(r"/book/(\d+)/", book_url).group(1))
        else:
            toc_url, book_id = f"{BASE}/book/{args.book}/", args.book
        chapters = chapter_list(fetch(toc_url), book_id)
        for pos, _id, title, _url in chapters:
            t = to_simplified(cc, title)[0] if cc else title
            print(f"{pos:>5}  {t}")
        return

    url = resolve_start_url(args)

    if args.plain:
        page = fetch(url)
        book, title, text, *_ = extract_chapter(page, url)
        if cc:
            book, title, text = to_simplified(cc, book, title, text)
        print(f"{book}\n{title}\n\n{text}\n")
        return

    Reader(url, cc, args.pad, args.theme).run()


if __name__ == "__main__":
    main()
