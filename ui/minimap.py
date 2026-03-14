import tkinter as tk


class MiniMap(tk.Canvas):
    def __init__(self, master, get_text_fn, yview_fn, scroll_to_fn, **kwargs):
        super().__init__(master, **kwargs)
        self.get_text = get_text_fn
        self.get_yview = yview_fn
        self.scroll_to = scroll_to_fn
        self.bind("<Button-1>", self._on_click)

    def refresh(self):
        self.delete("all")
        text = self.get_text()
        lines = text.splitlines()
        total = max(len(lines), 1)
        h = max(self.winfo_height(), 1)
        w = max(self.winfo_width(), 1)
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith("#"):
                y = int(i / total * h)
                self.create_line(0, y, w, y, fill="#374151")
        first, last = self.get_yview()
        y0 = int(first * h)
        y1 = max(y0 + 6, int(last * h))
        self.create_rectangle(0, y0, w, y1, outline="#3b82f6")

    def _on_click(self, event):
        h = max(self.winfo_height(), 1)
        ratio = min(max(event.y / h, 0.0), 1.0)
        self.scroll_to(ratio)
