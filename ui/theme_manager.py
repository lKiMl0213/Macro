class ThemeManager:
    def __init__(self, initial="dark"):
        self._themes = {
            "dark": {
                "background": "#0b0f14",
                "panel": "#111827",
                "panel_alt": "#0f172a",
                "panel_border": "#1f2937",
                "text": "#e5e7eb",
                "text_muted": "#9ca3af",
                "accent": "#3b82f6",
                "hover": "#1f2937",
                "button_bg": "#1f2937",
                "button_bg_alt": "#0f172a",
                "icon_tint": "#cbd5e1",
                "danger": "#ef4444",
            },
            "light": {
                "background": "#f5f7fb",
                "panel": "#ffffff",
                "panel_alt": "#f0f4f8",
                "panel_border": "#dbe2ea",
                "text": "#1f2937",
                "text_muted": "#6b7280",
                "accent": "#2563eb",
                "hover": "#e5e7eb",
                "button_bg": "#e2e8f0",
                "button_bg_alt": "#f1f5f9",
                "icon_tint": "#374151",
                "danger": "#ef4444",
            },
        }
        self._subscribers = []
        self._current = initial if initial in self._themes else "dark"

    def get(self):
        return self._themes[self._current]

    def set_theme(self, name):
        if name not in self._themes:
            return
        self._current = name
        theme = self.get()
        for cb in list(self._subscribers):
            cb(theme)

    def toggle(self):
        self.set_theme("light" if self._current == "dark" else "dark")

    def subscribe(self, callback):
        if callback not in self._subscribers:
            self._subscribers.append(callback)
        callback(self.get())

    def current_name(self):
        return self._current
