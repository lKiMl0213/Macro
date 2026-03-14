import tkinter as tk
import customtkinter as ctk

from .layout_system import ROW_HEIGHT, SCROLLBAR_THICK


COMMAND_ICON = {
    "CLICK": "record",
    "IMG_CLICK": "image",
    "IMG_CLICK_ANY": "image",
    "IMG_WAIT": "image",
    "WAIT": "play",
    "REGION": "region",
    "LABEL": "insert",
    "KEY_DOWN": "console",
    "KEY_UP": "console",
    "GOTO": "insert",
    "IF_FOUND": "insert",
    "IF_NOT_FOUND": "insert",
}


class VirtualTimeline(ctk.CTkFrame):
    def __init__(self, master, icon_engine, theme_manager, on_select=None, on_reorder=None, **kwargs):
        super().__init__(master, **kwargs)
        self.icon_engine = icon_engine
        self.theme_manager = theme_manager
        self.on_select = on_select
        self.on_reorder = on_reorder
        self._theme = None

        self._commands = []
        self._breakpoints = set()
        self._selected_line = None
        self._playhead_line = None
        self._slots = []
        self._icon_cache = {}
        self._drag_src = None
        self._drag_indicator = None
        self._render_job = None
        self._scroll_w = 0
        self._scroll_h = 0

        self._build()
        self.theme_manager.subscribe(self.apply_theme)

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.title = ctk.CTkLabel(self, text="Timeline")
        self.title.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_scrollbar, width=SCROLLBAR_THICK)
        self.scroll.grid(row=1, column=1, sticky="ns", pady=6)
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

    def apply_theme(self, theme):
        self._theme = theme
        self.configure(fg_color=theme["panel"])
        self.canvas.configure(bg=theme["panel"])
        self.title.configure(text_color=theme["text"])
        self._icon_cache.clear()
        self._schedule_render()

    def set_commands(self, commands):
        self._commands = commands or []
        self._update_scrollregion(force=True)
        self._schedule_render()

    def set_breakpoints(self, bps):
        self._breakpoints = set(bps or [])
        self._schedule_render()

    def highlight_line(self, line_no):
        self._selected_line = line_no
        self._schedule_render()

    def set_playhead(self, line_no):
        self._playhead_line = line_no
        self._schedule_render()

    def _on_scroll(self, first, last):
        try:
            first_f = float(first)
            last_f = float(last)
        except Exception:
            return
        try:
            self.scroll.set(first_f, last_f)
        except Exception:
            pass
        self._schedule_render()

    def _on_scrollbar(self, *args):
        self.canvas.yview(*args)
        self._schedule_render()

    def _schedule_render(self):
        if self._render_job is not None:
            return
        self._render_job = self.after_idle(self._render_visible)

    def _on_mousewheel(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")
        return "break"

    def _on_canvas_configure(self, _event=None):
        self._update_scrollregion(force=True)
        self._schedule_render()

    def _update_scrollregion(self, force=False):
        height = max(len(self._commands) * ROW_HEIGHT, 1)
        width = max(self.canvas.winfo_width(), 1)
        if not force and height == self._scroll_h and width == self._scroll_w:
            return
        self._scroll_h = height
        self._scroll_w = width
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def _ensure_slots(self):
        visible = max(int(self.canvas.winfo_height() / ROW_HEIGHT) + 2, 1)
        while len(self._slots) < visible:
            slot = self._create_slot()
            self._slots.append(slot)

    def _create_slot(self):
        y0 = 0
        y1 = ROW_HEIGHT
        rect = self.canvas.create_rectangle(0, y0, 10, y1, outline="")
        order_text = self.canvas.create_text(12, y0 + ROW_HEIGHT / 2, anchor="w")
        icon = self.canvas.create_image(52, y0 + ROW_HEIGHT / 2, anchor="center")
        cmd_text = self.canvas.create_text(72, y0 + ROW_HEIGHT / 2, anchor="w")
        bp_dot = self.canvas.create_oval(4, y0 + 12, 10, y0 + 18)
        return {
            "rect": rect,
            "order": order_text,
            "icon": icon,
            "cmd": cmd_text,
            "bp": bp_dot,
            "image": None,
        }

    def _render_visible(self):
        self._render_job = None
        if not self._theme:
            return
        self._ensure_slots()
        y_top = self.canvas.canvasy(0)
        first_index = int(y_top / ROW_HEIGHT)
        width = self.canvas.winfo_width()

        for i, slot in enumerate(self._slots):
            data_index = first_index + i
            if data_index < 0 or data_index >= len(self._commands):
                self._hide_slot(slot)
                continue

            line_no, line_text = self._commands[data_index]
            y0 = data_index * ROW_HEIGHT
            y1 = y0 + ROW_HEIGHT
            self.canvas.coords(slot["rect"], 0, y0, width, y1)
            self.canvas.coords(slot["order"], 12, y0 + ROW_HEIGHT / 2)
            self.canvas.coords(slot["icon"], 52, y0 + ROW_HEIGHT / 2)
            self.canvas.coords(slot["cmd"], 72, y0 + ROW_HEIGHT / 2)
            self.canvas.coords(slot["bp"], 4, y0 + 12, 10, y0 + 18)

            bg = self._theme["panel_alt"]
            if line_no == self._selected_line:
                bg = self._theme["hover"]
            if line_no == self._playhead_line:
                bg = self._theme["accent"]
            self.canvas.itemconfigure(slot["rect"], fill=bg)

            order_text = f"{data_index + 1:02d}"
            self.canvas.itemconfigure(slot["order"], text=order_text, fill=self._theme["text_muted"])

            cmd = line_text.strip().split()[0].upper() if line_text.strip() else ""
            icon_name = COMMAND_ICON.get(cmd, "insert")
            icon = self._get_icon(icon_name)
            self.canvas.itemconfigure(slot["icon"], image=icon)
            slot["image"] = icon

            self.canvas.itemconfigure(slot["cmd"], text=cmd, fill=self._theme["text"])
            if line_no in self._breakpoints:
                self.canvas.itemconfigure(slot["bp"], fill="#ef4444", outline="")
            else:
                self.canvas.itemconfigure(slot["bp"], fill="", outline="")

            for item in (slot["rect"], slot["order"], slot["icon"], slot["cmd"], slot["bp"]):
                self.canvas.itemconfigure(item, state="normal")

    def _hide_slot(self, slot):
        for item in (slot["rect"], slot["order"], slot["icon"], slot["cmd"], slot["bp"]):
            self.canvas.itemconfigure(item, state="hidden")

    def _get_icon(self, name):
        if name in self._icon_cache:
            return self._icon_cache[name]
        icon = self.icon_engine.get_photo(name, 16, theme=self._theme)
        self._icon_cache[name] = icon
        return icon

    def _index_from_y(self, y):
        return int(self.canvas.canvasy(y) // ROW_HEIGHT)

    def _on_click(self, event):
        idx = self._index_from_y(event.y)
        if 0 <= idx < len(self._commands):
            line_no, _ = self._commands[idx]
            self.highlight_line(line_no)
            if callable(self.on_select):
                self.on_select(line_no)

    def _on_drag_start(self, event):
        self._drag_src = self._index_from_y(event.y)

    def _on_drag_motion(self, event):
        if self._drag_src is None:
            return
        target = self._index_from_y(event.y)
        if target < 0 or target >= len(self._commands):
            return
        y = target * ROW_HEIGHT
        if self._drag_indicator is None:
            self._drag_indicator = self.canvas.create_line(0, y, self.canvas.winfo_width(), y, fill=self._theme["accent"])
        else:
            self.canvas.coords(self._drag_indicator, 0, y, self.canvas.winfo_width(), y)

    def _on_drag_end(self, event):
        if self._drag_indicator is not None:
            self.canvas.delete(self._drag_indicator)
            self._drag_indicator = None
        if self._drag_src is None:
            return
        target = self._index_from_y(event.y)
        src = self._drag_src
        self._drag_src = None
        if target < 0 or target >= len(self._commands) or target == src:
            return
        if callable(self.on_reorder):
            self.on_reorder(src, target)
