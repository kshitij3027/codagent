"""Rich-based display layer for terminal output.

Owns the Rich Console singleton and provides methods for rendering
styled panels, a thinking spinner, and streaming displays for both
model tokens and tool output lines.

All terminal output flows through this module. No bare print() calls
should exist elsewhere in the codebase — use Display methods instead.
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text


# Panel style configurations for each interaction type.
# Each entry defines border color, title (with emoji icon), and box style.
PANEL_STYLES: dict[str, dict] = {
    "user": {
        "border_style": "bright_cyan",
        "title": "\u276f You",
        "box": box.ROUNDED,
    },
    "response": {
        "border_style": "bright_green",
        "title": "\U0001f9e0 Assistant",
        "box": box.ROUNDED,
    },
    "tool_call": {
        "border_style": "bright_yellow",
        "title": "\U0001f6e0\ufe0f  Tool Call",
        "box": box.HEAVY,
    },
    "tool_output": {
        "border_style": "bright_magenta",
        "title": "\U0001f4cb Output",
        "box": box.ROUNDED,
    },
}


def _build_panel(content, panel_type: str) -> Panel:
    """Build a Panel with the correct style from PANEL_STYLES.

    Args:
        content: A Rich renderable (Text, Markdown, str, etc.).
        panel_type: One of the keys in PANEL_STYLES.

    Returns:
        A styled Panel instance.
    """
    style = PANEL_STYLES[panel_type]
    return Panel(
        content,
        title=style["title"],
        title_align="left",
        border_style=style["border_style"],
        box=style["box"],
        expand=True,
        padding=(1, 2),
    )


class Display:
    """Rich display layer for the coding agent terminal UI.

    Owns a singleton Console instance. Provides methods for:
    - Static panel rendering (show_panel)
    - Thinking spinner with flicker-free transition (show_spinner / hide_spinner)
    - Token-by-token response streaming (start_response_stream / stream_token / finish_response_stream)
    - Line-by-line tool output streaming (start_tool_output_stream / stream_tool_line / finish_tool_output_stream)
    """

    def __init__(self) -> None:
        self.console = Console()
        self._live: Live | None = None
        self._buffer: str = ""
        self._tool_buffer: str = ""
        self._streaming: bool = False
        self._spinner_active: bool = False

    # ------------------------------------------------------------------
    # Static panel rendering
    # ------------------------------------------------------------------

    def show_panel(self, content: str, panel_type: str) -> None:
        """Render a static panel to the console.

        For 'response' type, content is rendered as Markdown with syntax
        highlighting. For all other types, content is rendered as plain text.

        Args:
            content: The text content to display.
            panel_type: One of 'user', 'response', 'tool_call', 'tool_output'.
        """
        if panel_type not in PANEL_STYLES:
            raise ValueError(
                f"Unknown panel_type '{panel_type}'. "
                f"Must be one of: {', '.join(PANEL_STYLES.keys())}"
            )

        if panel_type == "response":
            renderable = Markdown(content, code_theme="monokai")
        else:
            renderable = Text(content)

        panel = _build_panel(renderable, panel_type)
        self.console.print(panel)

    # ------------------------------------------------------------------
    # Thinking spinner
    # ------------------------------------------------------------------

    def show_spinner(self, label: str = "Thinking...") -> None:
        """Start a thinking spinner using Live display.

        The spinner uses a Live context so it can be seamlessly replaced
        by the streaming response — no flicker from stopping and restarting.

        Args:
            label: Text displayed alongside the spinner animation.
        """
        spinner = Spinner("dots", text=Text(f"\U0001f9e0 {label}", style="bold cyan"))
        self._live = Live(
            spinner,
            console=self.console,
            refresh_per_second=12,
            transient=False,
        )
        self._live.start()
        self._spinner_active = True

    def hide_spinner(self) -> None:
        """Transition from spinner to response streaming.

        Instead of stopping the Live context (which causes flicker),
        this swaps the renderable to an empty response panel and sets
        a flag so start_response_stream() knows to reuse the Live instance.

        If no spinner is active, this is a no-op.
        """
        if not self._spinner_active:
            return

        self._spinner_active = False
        # Swap renderable to empty response panel — keeps Live alive
        if self._live is not None:
            empty_panel = _build_panel(Text(""), "response")
            self._live.update(empty_panel)

    # ------------------------------------------------------------------
    # Token-by-token response streaming
    # ------------------------------------------------------------------

    def start_response_stream(self) -> None:
        """Begin streaming a model response.

        If a Live context is already active (from the spinner), reuse it
        to avoid flicker. Otherwise, create a new Live context.

        Sets up the buffer and streaming state.
        """
        self._buffer = ""
        self._streaming = True

        if self._live is not None:
            # Reuse existing Live context (spinner-to-response transition)
            empty_panel = _build_panel(Text(""), "response")
            self._live.update(empty_panel)
        else:
            # No spinner was active — create fresh Live context
            empty_panel = _build_panel(Text(""), "response")
            self._live = Live(
                empty_panel,
                console=self.console,
                refresh_per_second=12,
                transient=False,
            )
            self._live.start()

    def stream_token(self, token: str) -> None:
        """Append a token to the streaming response buffer.

        Updates the Live display with plain Text (not Markdown) during
        streaming to avoid expensive re-rendering on every token.
        Final Markdown rendering happens in finish_response_stream().

        Args:
            token: The text token to append.
        """
        self._buffer += token
        if self._live is not None:
            panel = _build_panel(Text(self._buffer), "response")
            self._live.update(panel)

    def finish_response_stream(self) -> None:
        """Finalize the streaming response.

        Stops the Live display and prints a final static panel with
        full Markdown rendering (syntax highlighting, formatting).
        This gives the 'streaming looks plain, final render is rich' effect.

        If the buffer is empty, skips the final render.
        """
        if self._live is not None:
            self._live.stop()
            self._live = None

        if self._buffer:
            rendered = Markdown(self._buffer, code_theme="monokai")
            panel = _build_panel(rendered, "response")
            self.console.print(panel)

        self._buffer = ""
        self._streaming = False

    # ------------------------------------------------------------------
    # Line-by-line tool output streaming
    # ------------------------------------------------------------------

    def start_tool_output_stream(self) -> None:
        """Begin streaming tool output line by line.

        Creates a new Live context with an empty tool_output panel.
        """
        self._tool_buffer = ""
        empty_panel = _build_panel(Text(""), "tool_output")
        self._live = Live(
            empty_panel,
            console=self.console,
            refresh_per_second=12,
            transient=False,
        )
        self._live.start()

    def stream_tool_line(self, line: str) -> None:
        """Append a line to the tool output stream.

        Updates the Live display with the accumulated output.

        Args:
            line: The output line to append.
        """
        self._tool_buffer += line
        if self._live is not None:
            panel = _build_panel(Text(self._tool_buffer), "tool_output")
            self._live.update(panel)

    def finish_tool_output_stream(self) -> None:
        """Finalize the tool output stream.

        Stops the Live display and prints a final static tool_output panel.
        If the buffer is empty, skips the final render.
        """
        if self._live is not None:
            self._live.stop()
            self._live = None

        if self._tool_buffer:
            panel = _build_panel(Text(self._tool_buffer), "tool_output")
            self.console.print(panel)

        self._tool_buffer = ""
