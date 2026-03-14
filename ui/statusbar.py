import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, theme_manager=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._default_color = "#9ca3af"
        self._label = ctk.CTkLabel(self, text="Ready.", text_color=self._default_color)
        self._label.pack(fill="x", padx=8, pady=4)
        self._theme_manager = theme_manager
        if self._theme_manager:
            self._theme_manager.subscribe(self.apply_theme)

    def set(self, text, color=None):
        self._label.configure(text=text, text_color=color or self._default_color)

    def apply_theme(self, theme):
        self._default_color = theme["text_muted"]
        self._label.configure(text_color=self._default_color)
