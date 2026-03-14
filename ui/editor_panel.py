import re
import tkinter as tk
import customtkinter as ctk

from .layout_system import SCROLLBAR_THICK

try:
    from .minimap import MiniMap
except Exception:
    from minimap import MiniMap


class EditorPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        breakpoint_manager=None,
        on_line_selected=None,
        on_text_change=None,
        on_breakpoint_change=None,
        theme_manager=None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#111827", corner_radius=12, **kwargs)
        self._bp = breakpoint_manager
        self._on_line_selected = on_line_selected
        self._on_text_change = on_text_change
        self._on_breakpoint_change = on_breakpoint_change
        self._theme_manager = theme_manager
        self._theme = None
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        inner.rowconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)

        self._line_nums = tk.Text(
            inner,
            width=4,
            padx=6,
            pady=6,
            bg="#0f1115",
            fg="#6b7280",
            relief="flat",
            state="disabled",
            takefocus=0,
            font=("Consolas", 11),
        )
        self._line_nums.grid(row=0, column=0, sticky="ns")
        self._line_nums.tag_configure("bp", foreground="#ef4444")
        self._line_nums.bind("<Button-1>", self._toggle_breakpoint)

        self.text = tk.Text(
            inner,
            wrap=tk.NONE,
            font=("Consolas", 11),
            bg="#0f1115",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            selectbackground="#374151",
            selectforeground="#f9fafb",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#1f2937",
            highlightcolor="#3b82f6",
            padx=8,
            pady=6,
            undo=True,
        )
        self.text.grid(row=0, column=1, sticky="nsew")

        self.vbar = ctk.CTkScrollbar(
            inner, orientation=tk.VERTICAL, command=self._yview,
            width=SCROLLBAR_THICK, corner_radius=8, fg_color="#0b0f14",
            button_color="#374151", button_hover_color="#4b5563",
        )
        self.vbar.grid(row=0, column=2, sticky="ns", padx=(6, 0))
        self.hbar = ctk.CTkScrollbar(
            inner, orientation=tk.HORIZONTAL, command=self.text.xview,
            height=SCROLLBAR_THICK, corner_radius=8, fg_color="#0b0f14",
            button_color="#374151", button_hover_color="#4b5563",
        )
        self.hbar.grid(row=1, column=1, sticky="ew", pady=(6, 0))

        self.text.configure(
            yscrollcommand=lambda f, l: self._auto_scrollbar(self.vbar, f, l),
            xscrollcommand=lambda f, l: self._auto_scrollbar(self.hbar, f, l),
        )

        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", lambda e: self._on_activity(e, "key"))
        self.text.bind("<ButtonRelease-1>", lambda e: self._on_activity(e, "mouse"))
        self.text.bind("<MouseWheel>", lambda _e: self._sync_line_numbers())
        self.text.bind("<Configure>", lambda _e: self._sync_line_numbers())
        self.text.bind("<Button-3>", self._show_context_menu)

        self._highlight_job = None
        self._init_tags()

        self.minimap = MiniMap(
            inner,
            get_text_fn=self.get_text,
            yview_fn=self.text.yview,
            scroll_to_fn=self._scroll_to_ratio,
            width=12,
            bg="#0b0f14",
            highlightthickness=0,
        )
        self.minimap.grid(row=0, column=3, sticky="ns", padx=(6, 0))
        self._sync_line_numbers()

        self._menu = tk.Menu(self.text, tearoff=0, bg="#111827", fg="#e5e7eb")
        self._menu.add_command(label="Copy", command=lambda: self.text.event_generate("<<Copy>>"))
        self._menu.add_command(label="Paste", command=lambda: self.text.event_generate("<<Paste>>"))
        self._menu.add_command(label="Delete Line", command=self._delete_line)

        if self._theme_manager:
            self._theme_manager.subscribe(self.apply_theme)

    def _init_tags(self):
        if self._theme:
            self.text.tag_configure("command", foreground="#93c5fd")
            self.text.tag_configure("label", foreground="#fbbf24")
            self.text.tag_configure("path", foreground="#34d399")
            self.text.tag_configure("number", foreground="#fca5a5")
            self.text.tag_configure("breakpoint_line", background="#3b1f1f")
            self.text.tag_configure("current_line", background=self._theme["hover"])
        else:
            self.text.tag_configure("command", foreground="#93c5fd")
            self.text.tag_configure("label", foreground="#fbbf24")
            self.text.tag_configure("path", foreground="#34d399")
            self.text.tag_configure("number", foreground="#fca5a5")
            self.text.tag_configure("breakpoint_line", background="#3b1f1f")
            self.text.tag_configure("current_line", background="#1f2937")

    def apply_theme(self, theme):
        self._theme = theme
        self.configure(fg_color=theme["panel"])
        self._line_nums.configure(bg=theme["panel_alt"], fg=theme["text_muted"])
        self.text.configure(
            bg=theme["panel_alt"],
            fg=theme["text"],
            insertbackground=theme["text"],
            selectbackground=theme["hover"],
            selectforeground=theme["text"],
            highlightbackground=theme["panel_border"],
            highlightcolor=theme["accent"],
        )
        self.vbar.configure(
            fg_color=theme["background"],
            button_color=theme["panel_border"],
            button_hover_color=theme["hover"],
        )
        self.hbar.configure(
            fg_color=theme["background"],
            button_color=theme["panel_border"],
            button_hover_color=theme["hover"],
        )
        self.minimap.configure(bg=theme["background"])
        try:
            self.minimap.set_colors(theme["panel_border"], theme["accent"])
        except Exception:
            pass
        self._menu.configure(bg=theme["panel"], fg=theme["text"])
        self._init_tags()
        self._sync_line_numbers()

    def _auto_scrollbar(self, scrollbar, first, last):
        try:
            first_f = float(first)
            last_f = float(last)
        except Exception:
            scrollbar.set(first, last)
            return
        if first_f <= 0.0 and last_f >= 1.0:
            if scrollbar.winfo_ismapped():
                scrollbar.grid_remove()
        else:
            if not scrollbar.winfo_ismapped():
                scrollbar.grid()
        scrollbar.set(first_f, last_f)

    def _yview(self, *args):
        self.text.yview(*args)
        self._line_nums.yview(*args)

    def _on_modified(self, _event=None):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            self._sync_line_numbers()
            self._schedule_highlight()

    def _sync_line_numbers(self):
        line_count = int(self.text.index("end-1c").split(".")[0])
        lines = []
        for i in range(1, line_count + 1):
            dot = "●" if self._bp and self._bp.is_breakpoint(i) else " "
            lines.append(f"{dot} {i}")
        lines = "\n".join(lines)
        self._line_nums.configure(state="normal")
        self._line_nums.delete("1.0", "end")
        self._line_nums.insert("1.0", lines)
        if self._bp:
            for i in range(1, line_count + 1):
                if self._bp.is_breakpoint(i):
                    self._line_nums.tag_add("bp", f"{i}.0", f"{i}.1")
        self._line_nums.configure(state="disabled")
        self._line_nums.yview_moveto(self.text.yview()[0])
        self.text.tag_remove("breakpoint_line", "1.0", "end")
        if self._bp:
            for i in range(1, line_count + 1):
                if self._bp.is_breakpoint(i):
                    self.text.tag_add("breakpoint_line", f"{i}.0", f"{i}.end")
        self.minimap.refresh()

    def _schedule_highlight(self, _event=None):
        if self._highlight_job:
            try:
                self.after_cancel(self._highlight_job)
            except Exception:
                pass
        self._highlight_job = self.after(80, self._highlight)

    def _highlight(self):
        self._highlight_job = None
        for tag in ("command", "label", "path", "number"):
            self.text.tag_remove(tag, "1.0", "end")
        content = self.text.get("1.0", "end-1c")
        for i, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            leading = len(line) - len(line.lstrip())
            if stripped.upper().startswith("LABEL"):
                self.text.tag_add("label", f"{i}.0", f"{i}.end")
            parts = stripped.split()
            if parts:
                cmd_len = len(parts[0])
                start_col = leading
                self.text.tag_add("command", f"{i}.{start_col}", f"{i}.{start_col + cmd_len}")
            for match in re.finditer(r"([A-Za-z]:[\\/][^\s]+|\S+\.png|\S+\.jpg|\S+\.jpeg|\S+\.bmp|\S+\.gif)", line):
                self.text.tag_add("path", f"{i}.{match.start()}", f"{i}.{match.end()}")
            for match in re.finditer(r"\b\d+(?:\.\d+)?(?:ms|s)?\b", line):
                self.text.tag_add("number", f"{i}.{match.start()}", f"{i}.{match.end()}")
        if self._on_text_change:
            self._on_text_change()
        self.text.tag_raise("breakpoint_line")
        self.text.tag_raise("current_line")

    def _show_context_menu(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _delete_line(self):
        idx = self.text.index("insert").split(".")[0]
        self.text.delete(f"{idx}.0", f"{idx}.end+1c")
        self._sync_line_numbers()
        self._schedule_highlight()

    def set_current_line(self, line_number):
        self.text.tag_remove("current_line", "1.0", "end")
        if line_number and line_number > 0:
            self.text.tag_add("current_line", f"{line_number}.0", f"{line_number}.end")

    def set_line(self, line_no, text):
        self.text.delete(f"{line_no}.0", f"{line_no}.end")
        self.text.insert(f"{line_no}.0", text)
        self._sync_line_numbers()
        self._schedule_highlight()

    def insert_text(self, text):
        self.text.insert(tk.INSERT, text)
        self._sync_line_numbers()
        self._schedule_highlight()

    def get_text(self):
        return self.text.get("1.0", "end").rstrip("\n")

    def get_line(self, line_no):
        return self.text.get(f"{line_no}.0", f"{line_no}.end")

    def set_text(self, s):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", s)
        self._sync_line_numbers()
        self._schedule_highlight()

    def focus_editor(self):
        self.text.focus_set()

    def scroll_to_line(self, line_no):
        self.text.mark_set("insert", f"{line_no}.0")
        self.text.see(f"{line_no}.0")
        self.text.tag_remove("sel", "1.0", "end")
        self.text.tag_add("sel", f"{line_no}.0", f"{line_no}.end")
        self._sync_line_numbers()

    def _scroll_to_ratio(self, ratio):
        self.text.yview_moveto(ratio)
        self._line_nums.yview_moveto(ratio)
        self._sync_line_numbers()

    def _toggle_breakpoint(self, event):
        if not self._bp:
            return
        index = self._line_nums.index(f"@0,{event.y}")
        line_no = int(index.split(".")[0])
        self._bp.toggle(line_no)
        self._sync_line_numbers()
        if self._on_line_selected:
            self._on_line_selected(line_no)
        if self._on_breakpoint_change:
            self._on_breakpoint_change(self._bp.all())

    def _on_activity(self, _event=None, source="key"):
        self._schedule_highlight()
        if self._on_line_selected:
            idx = self.text.index("insert").split(".")[0]
            self._on_line_selected(int(idx), source)
