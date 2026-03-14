class StepController:
    def __init__(self, editor, timeline, status_cb):
        self.editor = editor
        self.timeline = timeline
        self.status_cb = status_cb
        self._lines = []
        self._index = -1
        self._active = False

    def load_from_text(self, text):
        lines = text.splitlines()
        self._lines = [i + 1 for i, line in enumerate(lines) if line.strip() and not line.strip().startswith("#")]
        if self._index >= len(self._lines):
            self._index = -1

    def step(self):
        if not self._lines:
            return None
        self._active = True
        self.status_cb("Step Mode")
        self._index = min(self._index + 1, len(self._lines) - 1)
        line_no = self._lines[self._index]
        self.editor.set_current_line(line_no)
        if self.timeline:
            if hasattr(self.timeline, "set_playhead"):
                self.timeline.set_playhead(line_no)
            else:
                self.timeline.highlight_line(line_no)
        return line_no

    def stop(self):
        self._active = False
        self._index = -1
        self.editor.set_current_line(0)
        if self.timeline:
            if hasattr(self.timeline, "set_playhead"):
                self.timeline.set_playhead(None)
            else:
                self.timeline.highlight_line(-1)
        self.status_cb("Ready.")

    def continue_run(self):
        self._active = False
        self.status_cb("Ready.")

    def is_active(self):
        return self._active
