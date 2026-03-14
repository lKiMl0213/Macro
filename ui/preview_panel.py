import os
import customtkinter as ctk
from PIL import Image


class PreviewPanel(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Image Preview")
        self.geometry("420x360")
        self.resizable(True, True)
        self._images = []
        self._current = 0
        self._zoom = 1.0

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        self.path_label = ctk.CTkLabel(top, text="", text_color="#e5e7eb")
        self.path_label.pack(anchor="w")
        self.param_label = ctk.CTkLabel(top, text="", text_color="#9ca3af")
        self.param_label.pack(anchor="w")

        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.zoom = ctk.CTkSlider(bottom, from_=0.3, to=2.0, number_of_steps=17, command=self._set_zoom)
        self.zoom.set(1.0)
        self.zoom.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.selector = ctk.CTkOptionMenu(bottom, values=["1"], command=self._select)
        self.selector.pack(side="left")

    def show(self, paths, params):
        self._images = [p for p in paths if os.path.exists(p)]
        if not self._images:
            return
        self._current = 0
        self.selector.configure(values=[str(i + 1) for i in range(len(self._images))])
        self.selector.set("1")
        self.path_label.configure(text=self._images[0])
        self.param_label.configure(text=params)
        self._zoom = 1.0
        self.zoom.set(1.0)
        self._render()
        self.deiconify()
        self.lift()

    def _render(self):
        path = self._images[self._current]
        img = Image.open(path)
        w, h = img.size
        scale = self._zoom
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self.image_label.configure(image=ctk_img)
        self.image_label.image = ctk_img

    def _set_zoom(self, value):
        self._zoom = float(value)
        if self._images:
            self._render()

    def _select(self, value):
        try:
            idx = int(value) - 1
        except Exception:
            return
        if 0 <= idx < len(self._images):
            self._current = idx
            self.path_label.configure(text=self._images[self._current])
            self._render()
