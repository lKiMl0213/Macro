import time


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


def hex_to_rgb(value):
    value = value.lstrip("#")
    if len(value) != 6:
        return (0, 0, 0)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def blend(c1, c2, t):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(
        (int(lerp(r1, r2, t)), int(lerp(g1, g2, t)), int(lerp(b1, b2, t)))
    )


class Animation:
    def __init__(self, widget, duration_ms=150, easing=ease_out_cubic):
        self.widget = widget
        self.duration = duration_ms / 1000.0
        self.easing = easing
        self._job = None
        self._start = 0.0
        self._from = 0.0
        self._to = 1.0
        self._update = None

    def start(self, from_value, to_value, update_cb):
        self.cancel()
        self._from = from_value
        self._to = to_value
        self._update = update_cb
        self._start = time.perf_counter()
        self._tick()

    def _tick(self):
        t = (time.perf_counter() - self._start) / self.duration if self.duration > 0 else 1.0
        t = clamp(t)
        eased = self.easing(t)
        value = lerp(self._from, self._to, eased)
        if self._update:
            self._update(value)
        if t < 1.0:
            self._job = self.widget.after(16, self._tick)
        else:
            self._job = None

    def cancel(self):
        if self._job:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
        self._job = None
