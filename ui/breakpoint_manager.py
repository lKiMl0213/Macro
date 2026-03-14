class BreakpointManager:
    def __init__(self):
        self._bps = set()

    def toggle(self, line_no):
        if line_no in self._bps:
            self._bps.remove(line_no)
            return False
        self._bps.add(line_no)
        return True

    def is_breakpoint(self, line_no):
        return line_no in self._bps

    def all(self):
        return sorted(self._bps)

    def clear(self):
        self._bps.clear()
