import tkinter as tk
import customtkinter as ctk

from .animation_utils import Animation, blend
from .layout_system import ICON_SIZES
from .tooltips import ToolTip


class IconButton(ctk.CTkFrame):
    def __init__(
        self,
        master,
        icon_engine,
        theme_manager,
        icon_name,
        text="",
        size="secondary",
        command=None,
        tooltip=None,
        corner_radius=10,
        padding=(8, 6),
        **kwargs,
    ):
        super().__init__(master, corner_radius=corner_radius, **kwargs)
        self.icon_engine = icon_engine
        self.theme_manager = theme_manager
        self.icon_name = icon_name
        self.text = text
        self.command = command
        self._state = "normal"
        self._hover = False
        self._pressed = False
        self._hover_progress = 0.0
        self._anim = Animation(self, duration_ms=160)
        self._size_px = ICON_SIZES.get(size, 20)
        self._padx, self._pady = padding
        self._theme = None

        self.grid_propagate(False)
        self.configure(cursor="hand2")
        self._build()
        self._bind_events()
        if tooltip:
            ToolTip(self, tooltip)

        self.theme_manager.subscribe(self.apply_theme)

    def _build(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=self._padx, pady=self._pady)

        self.icon_label = ctk.CTkLabel(self.container, text="")
        self.icon_label.pack(side="left")

        self.text_label = None
        if self.text:
            self.text_label = ctk.CTkLabel(self.container, text=self.text)
            self.text_label.pack(side="left", padx=(6, 0))

    def _bind_events(self):
        for w in (self, self.container, self.icon_label, self.text_label):
            if w is None:
                continue
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<ButtonPress-1>", self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<FocusOut>", self._on_blur)
        self.bind("<Return>", lambda _e: self._invoke())

    def apply_theme(self, theme):
        self._theme = theme
        self._update_visual(self._hover_progress)

    def set_state(self, state):
        self._state = state
        if state == "disabled":
            self._hover = False
            self._hover_progress = 0.0
        self._update_visual(self._hover_progress)

    def set_text(self, text):
        self.text = text
        if self.text_label:
            self.text_label.configure(text=text)
        else:
            self.text_label = ctk.CTkLabel(self.container, text=text)
            self.text_label.pack(side="left", padx=(6, 0))

    def _on_enter(self, _event=None):
        if self._state == "disabled":
            return
        self._hover = True
        self._anim.start(self._hover_progress, 1.0, self._update_visual)

    def _on_leave(self, _event=None):
        if self._state == "disabled":
            return
        self._hover = False
        self._anim.start(self._hover_progress, 0.0, self._update_visual)

    def _on_press(self, _event=None):
        if self._state == "disabled":
            return
        self._pressed = True
        self._update_visual(self._hover_progress)

    def _on_release(self, event=None):
        if self._state == "disabled":
            return
        was_pressed = self._pressed
        self._pressed = False
        self._update_visual(self._hover_progress)
        if was_pressed and self._hover:
            self._invoke()

    def _on_focus(self, _event=None):
        if self._theme:
            self.configure(border_width=2, border_color=self._theme["accent"])

    def _on_blur(self, _event=None):
        self.configure(border_width=0)

    def _invoke(self):
        if callable(self.command):
            self.command()

    def _update_visual(self, progress):
        self._hover_progress = progress
        if not self._theme:
            return
        base = self._theme["button_bg"]
        hover = self._theme["hover"]
        bg = blend(base, hover, progress)
        if self._pressed:
            bg = self._theme["panel_border"]
        if self._state == "disabled":
            bg = self._theme["button_bg_alt"]
        self.configure(fg_color=bg)

        brightness = 1.0 + (0.1 * progress)
        icon_state = self._state
        if self._pressed:
            icon_state = "active"
        icon = self.icon_engine.get_icon(
            self.icon_name,
            self._size_px,
            state=icon_state,
            theme=self._theme,
            brightness=brightness,
        )
        self.icon_label.configure(image=icon)
        self.icon_label.image = icon
        if self.text_label:
            self.text_label.configure(
                text_color=self._theme["text"] if self._state != "disabled" else self._theme["text_muted"]
            )
