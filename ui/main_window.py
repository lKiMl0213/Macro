import os
import tkinter as tk
import customtkinter as ctk

from .layout_system import BASE_UNIT, PANEL_PADDING, SECTION_SPACING
from .icon_engine import IconEngine
from .theme_manager import ThemeManager
from .icon_button import IconButton
from .timeline_virtualized import VirtualTimeline
from .editor_panel import EditorPanel
from .dock_panel import DockPanel
from .statusbar import StatusBar


class MainWindow:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.theme = ThemeManager("dark")
        self._theme = None
        self.icons = self._build_icon_engine()
        self._play_anim_job = None
        self._is_recording = False
        self._is_playing = False
        self._build()
        self.theme.subscribe(self.apply_theme)

    def _build_icon_engine(self):
        sprite_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sprite")
        sprite_path = os.path.join(sprite_dir, "iconpack.png")
        if not os.path.exists(sprite_path):
            alt = os.path.join(sprite_dir, "iconpack-removebg-preview.png")
            if os.path.exists(alt):
                sprite_path = alt
        icon_offset_x = 0
        icon_offset_y = 0
        return IconEngine(sprite_path, columns=6, rows=3, offset_x=icon_offset_x, offset_y=icon_offset_y)

    def _build(self):
        self.root.title("Macro Recorder")
        self.root.option_add("*Font", ("Segoe UI", 10))
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        self._build_toolbar()
        self._build_workspace()
        self._build_status()

        self.set_recording_state(False)
        self.set_playing_state(False)
        self.set_step_state(False)

        self.root.bind("<F8>", lambda _e: self.controller.start_recording())
        self.root.bind("<F9>", lambda _e: self.controller.play())
        self.root.bind("<F10>", lambda _e: self.controller.stop_execution())
        self.root.bind("<F6>", lambda _e: self.controller.step_forward())
        self.root.bind("<Control-e>", lambda _e: self.editor.focus_editor())

        self._size_to_content()

    def _build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.root, fg_color="transparent")
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=PANEL_PADDING, pady=(PANEL_PADDING, 8))

        self.toolbar_top = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.toolbar_top.pack(fill="x")

        self.toolbar_bottom = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        self.toolbar_bottom.pack(fill="x", pady=(8, 0))

        self.rec_frame, rec_inner = self._section(self.toolbar_top, "Recording")
        self.btn_record = IconButton(
            rec_inner,
            self.icons,
            self.theme,
            "record",
            text="Record",
            size="primary",
            command=self.controller.start_recording,
            tooltip="Record macro events",
        )
        self.btn_record.pack(side="left", padx=6)
        self.btn_stop = IconButton(
            rec_inner,
            self.icons,
            self.theme,
            "stop",
            text="Stop",
            size="primary",
            command=self.controller.stop_recording,
            tooltip="Stop recording",
        )
        self.btn_stop.pack(side="left", padx=6)
        self.record_indicator = ctk.CTkLabel(rec_inner, text="●")
        self.record_indicator.pack(side="left", padx=(6, 0))

        self.play_frame, play_inner = self._section(self.toolbar_top, "Playback")
        self.btn_play = IconButton(
            play_inner,
            self.icons,
            self.theme,
            "play",
            text="Play",
            size="primary",
            command=self.controller.play,
            tooltip="Play current macro",
        )
        self.btn_play.pack(side="left", padx=6)
        self.btn_step = IconButton(
            play_inner,
            self.icons,
            self.theme,
            "step",
            text="Step",
            size="secondary",
            command=self.controller.step_forward,
            tooltip="Step through macro",
        )
        self.btn_step.pack(side="left", padx=4)
        self.btn_continue = IconButton(
            play_inner,
            self.icons,
            self.theme,
            "continue",
            text="Continue",
            size="secondary",
            command=self.controller.continue_play,
            tooltip="Continue execution",
        )
        self.btn_continue.pack(side="left", padx=4)
        self.btn_stop_exec = IconButton(
            play_inner,
            self.icons,
            self.theme,
            "stop",
            text="Stop",
            size="secondary",
            command=self.controller.stop_execution,
            tooltip="Stop playback",
        )
        self.btn_stop_exec.pack(side="left", padx=4)

        self.lbl_speed = ctk.CTkLabel(play_inner, text="Speed")
        self.lbl_speed.pack(side="left", padx=(12, 4))
        self.speed_entry = ctk.CTkEntry(play_inner, width=70, textvariable=self.controller.speed_var)
        self.speed_entry.pack(side="left", padx=(12, 4))
        self.lbl_repeat = ctk.CTkLabel(play_inner, text="Repeat")
        self.lbl_repeat.pack(side="left", padx=(8, 4))
        self.repeat_entry = ctk.CTkEntry(play_inner, width=60, textvariable=self.controller.repeat_var)
        self.repeat_entry.pack(side="left", padx=4)

        self.files_frame, files_inner = self._section(self.toolbar_top, "Files")
        self.btn_save = IconButton(
            files_inner,
            self.icons,
            self.theme,
            "save",
            text="Save",
            size="secondary",
            command=self.controller.save,
            tooltip="Save macro to file",
        )
        self.btn_save.pack(side="left", padx=4)
        self.btn_load = IconButton(
            files_inner,
            self.icons,
            self.theme,
            "load",
            text="Load",
            size="secondary",
            command=self.controller.load,
            tooltip="Load macro from file",
        )
        self.btn_load.pack(side="left", padx=4)
        self.btn_folder = IconButton(
            files_inner,
            self.icons,
            self.theme,
            "folder",
            text="Screenshots",
            size="secondary",
            command=self.controller.open_capture_folder,
            tooltip="Open screenshot storage folder",
        )
        self.btn_folder.pack(side="left", padx=4)
        self.btn_theme = IconButton(
            files_inner,
            self.icons,
            self.theme,
            "theme",
            text="Theme",
            size="secondary",
            command=self.theme.toggle,
            tooltip="Toggle light/dark theme",
        )
        self.btn_theme.pack(side="left", padx=4)

        self.image_frame, image_inner = self._section(self.toolbar_bottom, "Image Tools")
        self.btn_image = IconButton(
            image_inner,
            self.icons,
            self.theme,
            "image",
            text="Image",
            size="secondary",
            command=self.controller.select_image,
            tooltip="Select image file",
        )
        self.btn_image.pack(side="left", padx=4)
        self.btn_capture = IconButton(
            image_inner,
            self.icons,
            self.theme,
            "capture",
            text="Capture",
            size="secondary",
            command=self.controller.capture_image,
            tooltip="Capture screen image",
        )
        self.btn_capture.pack(side="left", padx=4)
        self.btn_region = IconButton(
            image_inner,
            self.icons,
            self.theme,
            "region",
            text="Region",
            size="secondary",
            command=self.controller.select_region,
            tooltip="Select detection region",
        )
        self.btn_region.pack(side="left", padx=4)
        self.btn_clear_region = IconButton(
            image_inner,
            self.icons,
            self.theme,
            "clear",
            text="Clear",
            size="secondary",
            command=self.controller.clear_region,
            tooltip="Clear current region",
        )
        self.btn_clear_region.pack(side="left", padx=4)

        self.insert_frame, insert_inner = self._section(self.toolbar_bottom, "Insert")
        self.btn_insert_region = IconButton(
            insert_inner,
            self.icons,
            self.theme,
            "insert",
            text="REGION",
            size="secondary",
            command=self.controller.insert_region,
            tooltip="Insert REGION command",
        )
        self.btn_insert_region.pack(side="left", padx=4)
        self.btn_img_click = IconButton(
            insert_inner,
            self.icons,
            self.theme,
            "insert",
            text="IMG_CLICK",
            size="secondary",
            command=self.controller.insert_img_click,
            tooltip="Insert IMG_CLICK command",
        )
        self.btn_img_click.pack(side="left", padx=4)
        self.btn_img_click_any = IconButton(
            insert_inner,
            self.icons,
            self.theme,
            "insert",
            text="IMG_ANY",
            size="secondary",
            command=self.controller.insert_img_click_any,
            tooltip="Insert IMG_CLICK_ANY command",
        )
        self.btn_img_click_any.pack(side="left", padx=4)

        info_frame = ctk.CTkFrame(self.toolbar_bottom, fg_color="transparent")
        info_frame.pack(side="left", padx=SECTION_SPACING)
        self.lbl_image = ctk.CTkLabel(info_frame, textvariable=self.controller.image_var)
        self.lbl_image.pack(anchor="w")
        self.lbl_region = ctk.CTkLabel(info_frame, textvariable=self.controller.region_var)
        self.lbl_region.pack(anchor="w")

    def _build_workspace(self):
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=6, bd=0, relief="flat")
        self.main_pane.grid(row=1, column=0, sticky="nsew", padx=PANEL_PADDING, pady=(0, PANEL_PADDING))

        self.timeline_frame = ctk.CTkFrame(self.main_pane, corner_radius=12)
        self.timeline = VirtualTimeline(
            self.timeline_frame,
            icon_engine=self.icons,
            theme_manager=self.theme,
            on_select=self.controller.on_timeline_select,
            on_reorder=self.controller.on_timeline_reorder,
        )
        self.timeline.pack(fill="both", expand=True, padx=6, pady=6)
        self.main_pane.add(self.timeline_frame, minsize=220)

        self.workspace_frame = ctk.CTkFrame(self.main_pane, corner_radius=12)
        self.main_pane.add(self.workspace_frame)

        self.workspace_pane = tk.PanedWindow(self.workspace_frame, orient=tk.VERTICAL, sashwidth=6, bd=0, relief="flat")
        self.workspace_pane.pack(fill="both", expand=True, padx=6, pady=6)

        self.editor_frame = ctk.CTkFrame(self.workspace_pane, corner_radius=12)
        self.editor = EditorPanel(
            self.editor_frame,
            breakpoint_manager=self.controller.breakpoints,
            on_line_selected=self.controller.on_editor_line_selected,
            on_text_change=self.controller.on_editor_text_change,
            on_breakpoint_change=self.controller.on_breakpoints_changed,
            theme_manager=self.theme,
        )
        self.editor.pack(fill="both", expand=True, padx=6, pady=6)
        self.workspace_pane.add(self.editor_frame, minsize=240)

        self.dock_frame = ctk.CTkFrame(self.workspace_pane, corner_radius=12)
        self.dock = DockPanel(self.dock_frame, theme_manager=self.theme, on_properties_apply=self.controller.on_properties_apply)
        self.dock.pack(fill="both", expand=True)
        self.workspace_pane.add(self.dock_frame, minsize=180)
        self.properties = self.dock.properties

    def _build_status(self):
        self.status_bar = StatusBar(self.root, theme_manager=self.theme)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=PANEL_PADDING, pady=(0, 8))

    def _section(self, parent, title):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.pack(side="left", padx=SECTION_SPACING)
        label = ctk.CTkLabel(frame, text=title)
        label.pack(anchor="w", padx=8, pady=(6, 0))
        frame._title_label = label
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(padx=6, pady=6)
        return frame, inner

    def _size_to_content(self):
        try:
            self.root.update_idletasks()
            w = self.root.winfo_reqwidth()
            h = self.root.winfo_reqheight()
            if w > 0 and h > 0:
                self.root.minsize(w, h)
        except Exception:
            pass

    def apply_theme(self, theme):
        self._theme = theme
        ctk.set_appearance_mode("dark" if self.theme.current_name() == "dark" else "light")
        self.root.configure(fg_color=theme["background"])
        self.toolbar.configure(fg_color="transparent")
        self.toolbar_top.configure(fg_color="transparent")
        self.toolbar_bottom.configure(fg_color="transparent")
        for frame in (
            self.rec_frame,
            self.play_frame,
            self.files_frame,
            self.image_frame,
            self.insert_frame,
        ):
            frame.configure(fg_color=theme["panel"])
            if hasattr(frame, "_title_label"):
                frame._title_label.configure(text_color=theme["text"])
        self.record_indicator.configure(text_color=theme["text_muted"])
        self.lbl_image.configure(text_color=theme["text_muted"])
        self.lbl_region.configure(text_color=theme["text_muted"])
        self.lbl_speed.configure(text_color=theme["text_muted"])
        self.lbl_repeat.configure(text_color=theme["text_muted"])
        for entry in (self.speed_entry, self.repeat_entry):
            entry.configure(fg_color=theme["panel_alt"], border_color=theme["panel_border"])
        self.timeline_frame.configure(fg_color=theme["panel"])
        self.workspace_frame.configure(fg_color=theme["panel"])
        self.editor_frame.configure(fg_color=theme["panel"])
        self.dock_frame.configure(fg_color=theme["panel"])
        self.main_pane.configure(bg=theme["background"])
        self.workspace_pane.configure(bg=theme["background"])

    def set_recording_state(self, is_recording):
        self._is_recording = is_recording
        if is_recording:
            self.btn_record.set_state("disabled")
            self.btn_stop.set_state("normal")
            self.record_indicator.configure(text_color="#ef4444")
        else:
            self.btn_record.set_state("normal")
            self.btn_stop.set_state("disabled")
            if self._theme:
                self.record_indicator.configure(text_color=self._theme["text_muted"])

    def set_playing_state(self, is_playing):
        self._is_playing = is_playing
        if is_playing:
            self.btn_play.set_state("disabled")
            self._start_play_anim()
            self._set_controls_state("disabled", skip=(self.btn_stop_exec,))
            self.btn_stop_exec.set_state("normal")
            self.btn_record.set_state("disabled")
            self.btn_stop.set_state("disabled")
            self.speed_entry.configure(state="disabled")
            self.repeat_entry.configure(state="disabled")
        else:
            self.btn_play.set_state("normal")
            self._stop_play_anim()
            self._set_controls_state("normal")
            if self._is_recording:
                self.btn_record.set_state("disabled")
                self.btn_stop.set_state("normal")
            else:
                self.btn_record.set_state("normal")
                self.btn_stop.set_state("disabled")
            self.speed_entry.configure(state="normal")
            self.repeat_entry.configure(state="normal")

    def _set_controls_state(self, state, skip=()):
        for btn in (
            self.btn_image,
            self.btn_capture,
            self.btn_region,
            self.btn_clear_region,
            self.btn_insert_region,
            self.btn_img_click,
            self.btn_img_click_any,
            self.btn_save,
            self.btn_load,
            self.btn_folder,
            self.btn_step,
            self.btn_continue,
            self.btn_stop_exec,
        ):
            if btn in skip:
                continue
            btn.set_state(state)

    def _start_play_anim(self):
        self._stop_play_anim()
        self._play_anim_phase = 0

        def tick():
            if not self._is_playing:
                return
            dots = "." * (self._play_anim_phase % 3 + 1)
            self.btn_play.set_text(f"Playing{dots}")
            self._play_anim_phase += 1
            self._play_anim_job = self.root.after(450, tick)

        tick()

    def _stop_play_anim(self):
        if self._play_anim_job:
            try:
                self.root.after_cancel(self._play_anim_job)
            except Exception:
                pass
            self._play_anim_job = None
        self.btn_play.set_text("Play")

    def set_step_state(self, is_step):
        if is_step:
            self.btn_step.set_state("active")
        else:
            self.btn_step.set_state("normal")

    def set_status(self, text, color=None):
        self.status_bar.set(text, color=color)
