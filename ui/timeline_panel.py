import tkinter as tk
import customtkinter as ctk


COMMAND_ICONS = {
    "CLICK": "🖱",
    "IMG_CLICK": "🖼",
    "IMG_CLICK_ANY": "🖼",
    "WAIT": "⏱",
    "REGION": "▭",
    "LABEL": "🏷",
    "KEY_DOWN": "⌨",
    "KEY_UP": "⌨",
    "GOTO": "↪",
    "IF_FOUND": "✔",
    "IF_NOT_FOUND": "✖",
}


class TimelinePanel(ctk.CTkFrame):
    def __init__(self, master, on_select, on_reorder, **kwargs):
        super().__init__(master, fg_color="#111827", corner_radius=12, **kwargs)
        self.on_select = on_select
        self.on_reorder = on_reorder

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Timeline", text_color="#e5e7eb")
        title.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))

        self.canvas = tk.Canvas(self, bg="#111827", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.scroll = ctk.CTkScrollbar(
            self, orientation=tk.VERTICAL, command=self.canvas.yview,
            width=10, corner_radius=8, fg_color="#0b0f14",
            button_color="#374151", button_hover_color="#4b5563",
        )
        self.scroll.grid(row=1, column=1, sticky="ns", pady=6)
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.inner = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.items = []
        self._drag_index = None
        self._drag_target = None

    def _on_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def refresh(self, commands):
        for child in self.inner.winfo_children():
            child.destroy()
        self.items = []
        for idx, (line_no, line_text) in enumerate(commands, start=1):
            parts = line_text.strip().split()
            cmd = parts[0].upper() if parts else ""
            icon = COMMAND_ICONS.get(cmd, "•")
            duration = parts[1] if cmd == "WAIT" and len(parts) >= 2 else None
            row = ctk.CTkFrame(self.inner, fg_color="#0f172a", corner_radius=8, border_width=0)
            row.pack(fill="x", padx=6, pady=4)
            label = ctk.CTkLabel(
                row,
                text=f"{idx:02d} {icon} {cmd}",
                text_color="#e5e7eb",
            )
            label.pack(side="left", padx=8, pady=6)
            if duration:
                ctk.CTkLabel(row, text=duration, text_color="#9ca3af").pack(side="right", padx=8)
            row.bind("<Button-1>", lambda e, ln=line_no: self.on_select(ln))
            label.bind("<Button-1>", lambda e, ln=line_no: self.on_select(ln))
            row.bind("<ButtonPress-1>", lambda e, i=idx - 1: self._start_drag(i))
            row.bind("<ButtonRelease-1>", lambda e, i=idx - 1: self._end_drag(i))
            row.bind("<B1-Motion>", self._drag_motion)
            self.items.append((row, line_no))

    def highlight_line(self, line_no):
        for row, ln in self.items:
            if ln == line_no:
                row.configure(fg_color="#1f2937")
            else:
                row.configure(fg_color="#0f172a")

    def _start_drag(self, index):
        self._drag_index = index

    def _drag_motion(self, event):
        if self._drag_index is None:
            return
        y = event.widget.winfo_rooty() + event.y
        target = None
        for i, (row, _ln) in enumerate(self.items):
            ry = row.winfo_rooty()
            rh = row.winfo_height()
            if ry <= y <= ry + rh:
                target = i
                break
        for i, (row, _ln) in enumerate(self.items):
            if i == target:
                row.configure(fg_color="#1f2937", border_width=1, border_color="#3b82f6")
            else:
                row.configure(fg_color="#0f172a", border_width=0)
        self._drag_target = target

    def _end_drag(self, _index):
        if self._drag_index is None:
            return
        for row, _ln in self.items:
            row.configure(fg_color="#0f172a", border_width=0)
        y = self.canvas.winfo_pointery()
        target = None
        for i, (row, _ln) in enumerate(self.items):
            ry = row.winfo_rooty()
            rh = row.winfo_height()
            if ry <= y <= ry + rh:
                target = i
                break
        src = self._drag_index
        self._drag_index = None
        if target is None or target == src:
            return
        self.on_reorder(src, target)
