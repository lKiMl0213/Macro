import shlex
import customtkinter as ctk


class PropertiesPanel(ctk.CTkFrame):
    def __init__(self, master, on_apply, theme_manager=None, **kwargs):
        super().__init__(master, fg_color="#111827", corner_radius=12, **kwargs)
        self.on_apply = on_apply
        self._line_no = None
        self._cmd = None
        self._fields = {}
        self._theme_manager = theme_manager
        self._theme = None

        self.title = ctk.CTkLabel(self, text="Properties", text_color="#e5e7eb")
        self.title.pack(anchor="w", padx=10, pady=(8, 0))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=6, pady=6)
        self.apply_btn = ctk.CTkButton(
            self, text="Apply", command=self._apply,
            fg_color="#1f2937", hover_color="#374151",
            corner_radius=8, height=28
        )
        self.apply_btn.pack(anchor="e", padx=8, pady=(0, 8))

        if self._theme_manager:
            self._theme_manager.subscribe(self.apply_theme)

    def show_for_line(self, line_no, line_text):
        for child in self.body.winfo_children():
            child.destroy()
        self._fields = {}
        self._line_no = line_no
        cmd, args = self._parse(line_text)
        self._cmd = cmd
        if not cmd:
            return
        if cmd == "CLICK":
            self._field("Button", "button", args[0] if args else "left")
            if len(args) >= 3:
                self._field("X", "x", args[1])
                self._field("Y", "y", args[2])
        elif cmd == "WAIT":
            self._field("Duration", "duration", args[0] if args else "100ms")
        elif cmd == "REGION":
            if len(args) >= 4:
                self._field("X", "x", args[0])
                self._field("Y", "y", args[1])
                self._field("W", "w", args[2])
                self._field("H", "h", args[3])
        elif cmd in ("IMG_CLICK", "IMG_WAIT"):
            self._field("Image Path", "path", self._quote_arg(args[0]) if args else "")
            self._field("Confidence", "confidence", self._extract_param(args, "confidence"))
            self._field("Timeout", "timeout", self._extract_param(args, "timeout"))
        elif cmd == "IMG_CLICK_ANY":
            quoted = [self._quote_arg(p) for p in self._extract_paths(args)]
            self._field("Image Paths", "paths", " ".join(quoted))
            self._field("Confidence", "confidence", self._extract_param(args, "confidence"))
            self._field("Timeout", "timeout", self._extract_param(args, "timeout"))
        elif cmd == "LABEL":
            self._field("Name", "name", args[0] if args else "")
        elif cmd in ("KEY_DOWN", "KEY_UP"):
            self._field("Key", "key", " ".join(args))

    def _field(self, label, key, value):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(row, text=label, text_color=self._theme["text_muted"] if self._theme else "#9ca3af").pack(anchor="w")
        entry = ctk.CTkEntry(
            row,
            fg_color=self._theme["panel_alt"] if self._theme else "#0f172a",
            border_color=self._theme["panel_border"] if self._theme else "#1f2937",
            corner_radius=8,
        )
        entry.insert(0, value or "")
        entry.pack(fill="x")
        self._fields[key] = entry

    def _apply(self):
        if not self._cmd or self._line_no is None:
            return
        cmd = self._cmd
        if cmd == "CLICK":
            button = self._fields.get("button").get() if "button" in self._fields else "left"
            x = self._fields.get("x").get() if "x" in self._fields else ""
            y = self._fields.get("y").get() if "y" in self._fields else ""
            new_line = f"CLICK {button} {x} {y}".strip()
        elif cmd == "WAIT":
            new_line = f"WAIT {self._fields['duration'].get()}"
        elif cmd == "REGION":
            new_line = f"REGION {self._fields['x'].get()} {self._fields['y'].get()} {self._fields['w'].get()} {self._fields['h'].get()}"
        elif cmd in ("IMG_CLICK", "IMG_WAIT"):
            path = self._fields["path"].get()
            conf = self._fields["confidence"].get()
            tout = self._fields["timeout"].get()
            parts = [cmd, self._quote_arg(path)]
            if conf:
                parts.append(f"confidence={conf}")
            if tout:
                parts.append(f"timeout={tout}")
            new_line = " ".join(parts)
        elif cmd == "IMG_CLICK_ANY":
            paths = self._fields["paths"].get()
            conf = self._fields["confidence"].get()
            tout = self._fields["timeout"].get()
            parts = [cmd] + [self._quote_arg(p) for p in self._split_paths(paths)]
            if conf:
                parts.append(f"confidence={conf}")
            if tout:
                parts.append(f"timeout={tout}")
            new_line = " ".join(parts)
        elif cmd == "LABEL":
            new_line = f"LABEL {self._fields['name'].get()}"
        elif cmd in ("KEY_DOWN", "KEY_UP"):
            new_line = f"{cmd} {self._fields['key'].get()}"
        else:
            return
        self.on_apply(self._line_no, new_line)

    def _parse(self, line):
        try:
            parts = shlex.split(line, posix=False)
        except Exception:
            parts = line.split()
        if not parts:
            return None, []
        return parts[0].upper(), parts[1:]

    def apply_theme(self, theme):
        self._theme = theme
        self.configure(fg_color=theme["panel"])
        self.apply_btn.configure(fg_color=theme["button_bg"], hover_color=theme["hover"])
        self.title.configure(text_color=theme["text"])
        for entry in self._fields.values():
            entry.configure(fg_color=theme["panel_alt"], border_color=theme["panel_border"])

    def _quote_arg(self, s):
        if s is None:
            return ""
        if s == "":
            return '""'
        if any(ch.isspace() for ch in s) or '"' in s:
            return '"' + s.replace('"', '\\"') + '"'
        return s

    def _split_paths(self, text):
        try:
            return shlex.split(text, posix=False)
        except Exception:
            return text.split()

    def _extract_param(self, args, name):
        for tok in args:
            if tok.lower().startswith(name + "="):
                return tok.split("=", 1)[1]
        return ""

    def _extract_paths(self, args):
        paths = []
        for tok in args:
            t = tok.lower()
            if "=" in t:
                continue
            if t.endswith("ms") or t.endswith("s"):
                continue
            try:
                float(t)
                continue
            except Exception:
                pass
            paths.append(tok)
        return paths
