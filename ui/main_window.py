import tkinter as tk
import customtkinter as ctk

from .icons import ICONS
from .tooltips import ToolTip
from .statusbar import StatusBar
from .editor_panel import EditorPanel
from .sections_recording import build_recording_section
from .sections_playback import build_playback_section
from .sections_files import build_files_section


class MainWindow:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.icons = ICONS
        self._build()

    def _build(self):
        self.root.configure(fg_color="#0b0f14")
        self.root.option_add("*Font", ("Segoe UI", 10))

        self.root.rowconfigure(4, weight=1)
        self.root.columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self.root, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        def tooltip(widget, text):
            ToolTip(widget, text)

        rec_frame, btn_record, btn_stop, indicator = build_recording_section(top, self.controller, self.icons, tooltip)
        rec_frame.pack(side=tk.LEFT, padx=6)
        self.btn_record = btn_record
        self.btn_stop = btn_stop
        self.record_indicator = indicator

        play_frame, btn_play, entry_speed, entry_repeat = build_playback_section(top, self.controller, self.icons, tooltip)
        play_frame.pack(side=tk.LEFT, padx=6)
        self.btn_play = btn_play
        self.entry_speed = entry_speed
        self.entry_repeat = entry_repeat

        files_frame, btn_save, btn_load, btn_folder = build_files_section(top, self.controller, self.icons, tooltip)
        files_frame.pack(side=tk.LEFT, padx=6)
        self.btn_save = btn_save
        self.btn_load = btn_load
        self.btn_folder = btn_folder

        image_row = ctk.CTkFrame(self.root, fg_color="transparent")
        image_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        image_frame = ctk.CTkFrame(image_row, fg_color="#111827", corner_radius=12)
        image_frame.pack(side=tk.LEFT, padx=6, fill="x")
        ctk.CTkLabel(image_frame, text="Image Tools", text_color="#e5e7eb").pack(anchor="w", padx=10, pady=(8, 0))
        image_inner = ctk.CTkFrame(image_frame, fg_color="transparent")
        image_inner.pack(fill="x", padx=6, pady=6)

        self.btn_image = ctk.CTkButton(
            image_inner,
            text=f"{self.icons['image']} Image...",
            command=self.controller.select_image,
            fg_color="#1f2937",
            hover_color="#374151",
            corner_radius=10,
            height=30,
        )
        self.btn_image.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_image, "Select image file")

        self.btn_capture = ctk.CTkButton(
            image_inner,
            text=f"{self.icons['capture']} Capture",
            command=self.controller.capture_image,
            fg_color="#1f2937",
            hover_color="#374151",
            corner_radius=10,
            height=30,
        )
        self.btn_capture.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_capture, "Capture screen image")

        self.btn_region = ctk.CTkButton(
            image_inner,
            text=f"{self.icons['region']} Region",
            command=self.controller.select_region,
            fg_color="#1f2937",
            hover_color="#374151",
            corner_radius=10,
            height=30,
        )
        self.btn_region.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_region, "Select detection region")

        self.btn_clear_region = ctk.CTkButton(
            image_inner,
            text=f"{self.icons['clear']} Clear Region",
            command=self.controller.clear_region,
            fg_color="#0f172a",
            hover_color="#1f2937",
            corner_radius=8,
            height=26,
        )
        self.btn_clear_region.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_clear_region, "Clear current region")

        insert_row = ctk.CTkFrame(self.root, fg_color="transparent")
        insert_row.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 6))
        insert_frame = ctk.CTkFrame(insert_row, fg_color="#111827", corner_radius=12)
        insert_frame.pack(side=tk.LEFT, padx=6, fill="x")
        ctk.CTkLabel(insert_frame, text="Insert Commands", text_color="#e5e7eb").pack(anchor="w", padx=10, pady=(8, 0))
        insert_inner = ctk.CTkFrame(insert_frame, fg_color="transparent")
        insert_inner.pack(fill="x", padx=6, pady=6)

        self.btn_insert_region = ctk.CTkButton(
            insert_inner,
            text=f"{self.icons['insert']} Insert REGION",
            command=self.controller.insert_region,
            fg_color="#0f172a",
            hover_color="#1f2937",
            corner_radius=8,
            height=26,
        )
        self.btn_insert_region.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_insert_region, "Insert REGION command")

        self.btn_img_click = ctk.CTkButton(
            insert_inner,
            text=f"{self.icons['insert']} Insert IMG_CLICK",
            command=self.controller.insert_img_click,
            fg_color="#0f172a",
            hover_color="#1f2937",
            corner_radius=8,
            height=26,
        )
        self.btn_img_click.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_img_click, "Insert IMG_CLICK command")

        self.btn_img_click_any = ctk.CTkButton(
            insert_inner,
            text=f"{self.icons['insert']} Insert IMG_CLICK_ANY",
            command=self.controller.insert_img_click_any,
            fg_color="#0f172a",
            hover_color="#1f2937",
            corner_radius=8,
            height=26,
        )
        self.btn_img_click_any.pack(side="left", padx=4, pady=4)
        tooltip(self.btn_img_click_any, "Insert IMG_CLICK_ANY command")

        info_row = ctk.CTkFrame(self.root, fg_color="transparent")
        info_row.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        info_row.columnconfigure(0, weight=1)

        info_left = ctk.CTkFrame(info_row, fg_color="transparent")
        info_left.grid(row=0, column=0, sticky="w")
        self.lbl_image = ctk.CTkLabel(info_left, textvariable=self.controller.image_var, text_color="#9ca3af")
        self.lbl_image.pack(side=tk.LEFT, padx=4)
        self.lbl_region = ctk.CTkLabel(info_left, textvariable=self.controller.region_var, text_color="#9ca3af")
        self.lbl_region.pack(side=tk.LEFT, padx=12)

        self.editor = EditorPanel(self.root)
        self.editor.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 6))

        self.root.bind("<F8>", lambda _e: self.controller.start_recording())
        self.root.bind("<F9>", lambda _e: self.controller.play())
        self.root.bind("<F10>", lambda _e: self.controller.stop_recording())
        self.root.bind("<Control-e>", lambda _e: self.editor.focus_editor())

        self._size_to_content()

    def _size_to_content(self):
        try:
            self.root.update_idletasks()
            w = self.root.winfo_reqwidth()
            h = self.root.winfo_reqheight()
            if w > 0 and h > 0:
                self.root.minsize(w, h)
                self.root.geometry(f"{w}x{h}")
        except Exception:
            pass

    def set_recording_state(self, is_recording):
        if is_recording:
            self.btn_record.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.record_indicator.configure(text_color="#ef4444")
        else:
            self.btn_record.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.record_indicator.configure(text_color="#374151")

    def set_status(self, text):
        self.status_bar.set(text)
