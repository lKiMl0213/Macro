import os
import customtkinter as ctk
from PIL import Image

from .properties_panel import PropertiesPanel


class DockPanel(ctk.CTkFrame):
    def __init__(self, master, theme_manager, on_properties_apply=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme_manager = theme_manager
        self._theme = None
        self._preview_images = []
        self._preview_index = 0

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_properties = self.tabs.add("Properties")
        self.tab_preview = self.tabs.add("Preview")
        self.tab_breakpoints = self.tabs.add("Breakpoints")
        self.tab_console = self.tabs.add("Console")

        self.properties = PropertiesPanel(self.tab_properties, on_apply=on_properties_apply, theme_manager=theme_manager)
        self.properties.pack(fill="both", expand=True)

        self._build_preview()
        self._build_breakpoints()
        self._build_console()
        self.theme_manager.subscribe(self.apply_theme)

    def _build_preview(self):
        self.preview_header = ctk.CTkLabel(self.tab_preview, text="")
        self.preview_header.pack(anchor="w", padx=12, pady=(12, 0))
        self.preview_params = ctk.CTkLabel(self.tab_preview, text="")
        self.preview_params.pack(anchor="w", padx=12, pady=(0, 8))
        self.preview_image = ctk.CTkLabel(self.tab_preview, text="")
        self.preview_image.pack(fill="both", expand=True, padx=12, pady=8)
        controls = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        controls.pack(fill="x", padx=12, pady=(0, 12))
        self.preview_zoom = ctk.CTkSlider(controls, from_=0.3, to=2.0, number_of_steps=17, command=self._set_zoom)
        self.preview_zoom.set(1.0)
        self.preview_zoom.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.preview_selector = ctk.CTkOptionMenu(controls, values=["1"], command=self._select_preview)
        self.preview_selector.pack(side="left")

    def _build_breakpoints(self):
        self.bp_list = ctk.CTkTextbox(self.tab_breakpoints, height=120)
        self.bp_list.pack(fill="both", expand=True, padx=12, pady=12)
        self.bp_list.configure(state="disabled")

    def _build_console(self):
        self.console = ctk.CTkTextbox(self.tab_console, height=120)
        self.console.pack(fill="both", expand=True, padx=12, pady=12)
        self.console.configure(state="disabled")

    def apply_theme(self, theme):
        self._theme = theme
        self.configure(fg_color=theme["panel"])
        self.tabs.configure(fg_color=theme["panel"], segmented_button_fg_color=theme["panel_alt"])
        for label in (self.preview_header, self.preview_params):
            label.configure(text_color=theme["text_muted"])

    def show_preview(self, paths, params):
        self._preview_images = [p for p in paths if os.path.exists(p)]
        if not self._preview_images:
            return
        self._preview_index = 0
        self.preview_selector.configure(values=[str(i + 1) for i in range(len(self._preview_images))])
        self.preview_selector.set("1")
        self.preview_header.configure(text=self._preview_images[0])
        self.preview_params.configure(text=params)
        self.preview_zoom.set(1.0)
        self._render_preview()

    def _render_preview(self):
        path = self._preview_images[self._preview_index]
        img = Image.open(path)
        scale = float(self.preview_zoom.get())
        w, h = img.size
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.preview_image.configure(image=ctk_img)
        self.preview_image.image = ctk_img
        self.preview_header.configure(text=path)

    def _set_zoom(self, _value):
        if self._preview_images:
            self._render_preview()

    def _select_preview(self, value):
        try:
            idx = int(value) - 1
        except Exception:
            return
        if 0 <= idx < len(self._preview_images):
            self._preview_index = idx
            self._render_preview()

    def set_breakpoints(self, bps):
        self.bp_list.configure(state="normal")
        self.bp_list.delete("1.0", "end")
        for bp in bps:
            self.bp_list.insert("end", f"Line {bp}\n")
        self.bp_list.configure(state="disabled")

    def log(self, text):
        self.console.configure(state="normal")
        self.console.insert("end", text + "\n")
        self.console.configure(state="disabled")
