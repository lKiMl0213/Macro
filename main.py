from dataclasses import dataclass
from collections import namedtuple
import os
import shlex
import time
import threading
from threading import Event, Lock
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from pynput import mouse, keyboard
except Exception as e:
    mouse = None
    keyboard = None

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import mss
except Exception:
    mss = None

try:
    from pyscreeze import Box as PyscreezeBox
except Exception:
    PyscreezeBox = None

if PyscreezeBox is None:
    Box = namedtuple('Box', 'left top width height')
else:
    Box = PyscreezeBox

@dataclass
class MacroEvent:
    ts: float
    type: str
    payload: object

class EventStore:
    def __init__(self):
        self._events = []
        self._lock = Lock()

    def clear(self):
        with self._lock:
            self._events.clear()

    def append(self, ev: MacroEvent):
        with self._lock:
            self._events.append(ev)

    def snapshot(self):
        with self._lock:
            return list(self._events)

    def extend(self, events):
        with self._lock:
            self._events.extend(events)

    def __len__(self):
        with self._lock:
            return len(self._events)

class ScriptParser:
    @staticmethod
    def parse(text: str):
        parsed = []
        for raw in text.splitlines():
            s = raw.strip()
            if not s or s.startswith('#'):
                continue
            try:
                parts = shlex.split(s, posix=False)
            except Exception:
                parts = s.split()
            cmd = parts[0].upper()
            args = parts[1:]
            parsed.append((cmd, args))
        return parsed

    @staticmethod
    def parse_wait_token(tok: str) -> float:
        t = tok.lower()
        try:
            if t.endswith('ms'):
                return float(t[:-2]) / 1000.0
            if t.endswith('s'):
                return float(t[:-1])
            return float(t)
        except Exception:
            try:
                return float(t)
            except Exception:
                return 0.0

    @staticmethod
    def format_wait(delta_seconds: float):
        if delta_seconds < 0.001:
            return None
        if delta_seconds < 1.0:
            ms = int(round(delta_seconds * 1000))
            if ms <= 0:
                return None
            return f"WAIT {ms}ms"
        if abs(delta_seconds - round(delta_seconds)) < 1e-6:
            return f"WAIT {int(round(delta_seconds))}s"
        return f"WAIT {delta_seconds:.1f}s"

    @staticmethod
    def events_to_script(events):
        if not events:
            return ""
        evs = sorted(events, key=lambda e: e.ts)
        lines = []
        prev = evs[0].ts
        for ev in evs:
            wait = ev.ts - prev
            wline = ScriptParser.format_wait(wait)
            if wline:
                lines.append(wline)
            if ev.type == 'click':
                x, y, btn = ev.payload
                lines.append(f"CLICK {btn} {int(x)} {int(y)}")
            elif ev.type == 'key_down':
                lines.append(f"KEY_DOWN {ev.payload}")
            elif ev.type == 'key_up':
                lines.append(f"KEY_UP {ev.payload}")
            prev = ev.ts
        return "\n".join(lines)

    @staticmethod
    def script_to_events(parsed):
        base = time.time()
        t = base
        out = []
        delta_eps = 0.001
        for cmd, args in parsed:
            if cmd == 'WAIT':
                if not args:
                    continue
                w = ScriptParser.parse_wait_token(args[0])
                t += max(0.0, w)
            elif cmd == 'CLICK':
                btn = args[0] if len(args) >= 1 else 'left'
                if len(args) >= 3:
                    try:
                        x = int(args[1]); y = int(args[2])
                    except Exception:
                        x = y = None
                else:
                    x = y = None
                out.append(MacroEvent(t, 'click', (x, y, btn)))
                t += delta_eps
            elif cmd == 'KEY_DOWN':
                k = ' '.join(args)
                out.append(MacroEvent(t, 'key_down', k))
                t += delta_eps
            elif cmd == 'KEY_UP':
                k = ' '.join(args)
                out.append(MacroEvent(t, 'key_up', k))
                t += delta_eps
            else:
                t += delta_eps
        return out

def _is_number(tok: str) -> bool:
    try:
        float(tok)
        return True
    except Exception:
        return False

def _quote_arg(s: str) -> str:
    if s == "":
        return '""'
    if any(ch.isspace() for ch in s) or '"' in s:
        return '"' + s.replace('"', '\\"') + '"'
    return s

def get_virtual_screen_bounds():
    if mss is not None:
        try:
            with mss.mss() as sct:
                mon = sct.monitors[0]
                return mon['left'], mon['top'], mon['width'], mon['height']
        except Exception:
            pass
    if pyautogui is not None:
        try:
            w, h = pyautogui.size()
            return 0, 0, w, h
        except Exception:
            pass
    return 0, 0, 0, 0

class Recorder:
    def __init__(self, store: EventStore):
        self.store = store
        self._mouse = None
        self._keyboard = None
        self._running = False

    def _now_event(self, typ, payload):
        self.store.append(MacroEvent(time.time(), typ, payload))

    def _on_click(self, x, y, button, pressed):
        if pressed:
            btn = str(button).split('.')[-1]
            self._now_event('click', (int(x), int(y), btn))

    def _on_key_press(self, key):
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self._now_event('key_down', k)

    def _on_key_release(self, key):
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self._now_event('key_up', k)

    def start(self):
        if self._running:
            return
        if mouse is None or keyboard is None:
            raise RuntimeError('pynput is required for recording')
        self._mouse = mouse.Listener(on_click=self._on_click)
        self._keyboard = keyboard.Listener(on_press=self._on_key_press, on_release=self._on_key_release)
        self._mouse.start(); self._keyboard.start()
        self._running = True

    def stop(self):
        if not self._running:
            return
        try:
            if self._mouse:
                self._mouse.stop()
            if self._keyboard:
                self._keyboard.stop()
        finally:
            self._running = False

def select_screen_region(root):
    result = {'region': None}
    left0, top0, width0, height0 = get_virtual_screen_bounds()
    use_geometry = width0 > 0 and height0 > 0
    win = tk.Toplevel(root)
    if use_geometry:
        win.geometry(f"{width0}x{height0}{left0:+d}{top0:+d}")
    else:
        win.attributes('-fullscreen', True)
    win.attributes('-alpha', 0.3)
    win.attributes('-topmost', True)
    win.configure(bg='black')
    win.overrideredirect(True)

    canvas = tk.Canvas(win, bg='black', highlightthickness=0, cursor='cross')
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_text(12, 12, anchor='nw', fill='white',
                       text='Drag to select region. Esc to cancel.')

    offset = {'x': left0 if use_geometry else 0, 'y': top0 if use_geometry else 0}
    start = {'x': 0, 'y': 0}
    rect = {'id': None}

    def on_press(event):
        start['x'] = event.x
        start['y'] = event.y
        if rect['id'] is not None:
            canvas.delete(rect['id'])
        rect['id'] = canvas.create_rectangle(start['x'], start['y'], start['x'], start['y'],
                                             outline='red', width=2)

    def on_drag(event):
        if rect['id'] is None:
            return
        canvas.coords(rect['id'], start['x'], start['y'], event.x, event.y)

    def on_release(event):
        if rect['id'] is None:
            win.destroy()
            return
        x1, y1 = start['x'], start['y']
        x2, y2 = event.x, event.y
        left, top = min(x1, x2) + offset['x'], min(y1, y2) + offset['y']
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w >= 2 and h >= 2:
            result['region'] = (left, top, w, h)
        win.destroy()

    def on_cancel(_event=None):
        result['region'] = None
        win.destroy()

    win.bind('<Escape>', on_cancel)
    canvas.bind('<ButtonPress-1>', on_press)
    canvas.bind('<B1-Motion>', on_drag)
    canvas.bind('<ButtonRelease-1>', on_release)

    win.grab_set()
    win.wait_window()
    return result['region']

class Executor:
    def __init__(self):
        self._stop = Event()
        self._default_region = None
        self._region = None
        self._last_found = False

    def stop(self):
        self._stop.set()

    def reset(self):
        self._stop.clear()

    def set_default_region(self, region):
        self._default_region = region

    @staticmethod
    def _normalize_key(tok: str):
        tok = tok.strip()
        if tok.startswith('Key.'):
            tok = tok.split('.', 1)[1]
        return tok.replace("'", '').replace('"', '')

    @staticmethod
    def _is_not_found_exc(err) -> bool:
        return type(err).__name__ == 'ImageNotFoundException'

    def _grab_screen(self):
        try:
            from PIL import Image
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None, 0, 0
        if mss is not None:
            try:
                with mss.mss() as sct:
                    mon = sct.monitors[0]
                    left = mon['left']
                    top = mon['top']
                    width = mon['width']
                    height = mon['height']
                    img = sct.grab(mon)
                    screen = Image.frombytes('RGB', img.size, img.rgb)
                    return screen, left, top
            except Exception as e:
                print('Image locate error:', type(e).__name__, repr(e))
        if pyautogui is not None:
            try:
                screen = pyautogui.screenshot()
                return screen, 0, 0
            except Exception as e:
                print('Image locate error:', type(e).__name__, repr(e))
        return None, 0, 0

    def _grab_haystack(self):
        screen, sx, sy = self._grab_screen()
        if screen is None:
            return None, 0, 0
        if self._region:
            rx, ry, rw, rh = self._region
            left = max(0, rx - sx)
            top = max(0, ry - sy)
            right = min(screen.width, left + rw)
            bottom = min(screen.height, top + rh)
            if right <= left or bottom <= top:
                return None, 0, 0
            cropped = screen.crop((left, top, right, bottom))
            return cropped, sx + left, sy + top
        return screen, sx, sy

    def _locate_in_haystack(self, needle_img, haystack_img, offset_x, offset_y, confidence=None):
        try:
            if confidence is None:
                box = pyautogui.locate(needle_img, haystack_img)
            else:
                box = pyautogui.locate(needle_img, haystack_img, confidence=confidence)
        except Exception as e:
            if self._is_not_found_exc(e):
                return None
            msg = str(e).lower()
            if 'needle' in msg and 'haystack' in msg:
                return None
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        if not box:
            return None
        return Box(box.left + offset_x, box.top + offset_y, box.width, box.height)

    @staticmethod
    def _parse_img_args(args):
        if not args:
            return None, [], None, None, 'left', None
        path = args[0]
        paths = [path]
        timeout = None
        confidence = None
        button = 'left'
        scale = None
        for tok in args[1:]:
            t = tok.lower()
            if t.startswith('timeout='):
                timeout = ScriptParser.parse_wait_token(tok.split('=', 1)[1])
            elif t.startswith('conf=') or t.startswith('confidence='):
                try:
                    confidence = float(tok.split('=', 1)[1])
                except Exception:
                    confidence = None
            elif t.startswith('scale='):
                try:
                    scale = float(tok.split('=', 1)[1])
                except Exception:
                    scale = None
            elif t.startswith('button='):
                button = tok.split('=', 1)[1].lower()
            elif t in ('left', 'right', 'middle'):
                button = t
            elif _is_number(tok):
                if timeout is None:
                    timeout = ScriptParser.parse_wait_token(tok)
                elif confidence is None:
                    try:
                        confidence = float(tok)
                    except Exception:
                        confidence = None
            else:
                paths.append(tok)
        return path, paths, timeout, confidence, button, scale

    def _locate_image(self, path, confidence=None, scale=None):
        if not pyautogui:
            print('pyautogui not available for image matching')
            return None
        if scale is not None:
            return self._locate_image_scaled(path, confidence=confidence, scale=scale)
        try:
            from PIL import Image
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        try:
            img = Image.open(path)
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        img = img.convert('RGB')
        haystack, off_x, off_y = self._grab_haystack()
        if haystack is None:
            return None
        box = self._locate_in_haystack(img, haystack, off_x, off_y, confidence=confidence)
        if box:
            return box
        return self._locate_image_multiscale(path, confidence=confidence, haystack=haystack, offset_x=off_x, offset_y=off_y)

    def _build_scale_list(self, min_scale, max_scale):
        step = 0.1
        scales = []
        i = 0
        while True:
            down = 1.0 - (i * step)
            up = 1.0 + (i * step)
            added = False
            if down >= min_scale:
                scales.append(down)
                added = True
            if i > 0 and up <= max_scale:
                scales.append(up)
                added = True
            if not added and down < min_scale and up > max_scale:
                break
            i += 1
        # ensure bounds included
        scales.append(min_scale)
        scales.append(max_scale)
        out = []
        seen = set()
        for s in scales:
            s = round(s, 3)
            if s < min_scale or s > max_scale:
                continue
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
        return out

    def _locate_image_multiscale(self, path, confidence=None, haystack=None, offset_x=0, offset_y=0):
        try:
            from PIL import Image
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        try:
            img = Image.open(path)
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        img = img.convert('RGB')
        tw, th = img.size
        if haystack is None:
            haystack, offset_x, offset_y = self._grab_haystack()
        if haystack is None:
            return None
        hw, hh = haystack.size
        if tw <= 0 or th <= 0 or hw <= 0 or hh <= 0:
            return None
        max_fit = min(hw / tw, hh / th)
        max_scale = min(max_fit, 2.0)
        min_scale = 0.3
        if max_scale < min_scale:
            min_scale = max_scale
        if max_scale <= 0:
            return None
        scales = self._build_scale_list(min_scale, max_scale)
        for scale in scales:
            new_w = max(1, int(tw * scale))
            new_h = max(1, int(th * scale))
            if self._region and (new_w > hw or new_h > hh):
                continue
            if new_w == tw and new_h == th:
                resized = img
            else:
                resized = img.resize((new_w, new_h), Image.LANCZOS)
            box = self._locate_in_haystack(resized, haystack, offset_x, offset_y, confidence=confidence)
            if box:
                return box
        return None

    def _locate_image_scaled(self, path, confidence=None, scale=None):
        try:
            from PIL import Image
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        try:
            img = Image.open(path)
        except Exception as e:
            print('Image locate error:', type(e).__name__, repr(e))
            return None
        img = img.convert('RGB')
        tw, th = img.size
        if self._region:
            hw, hh = self._region[2], self._region[3]
        else:
            _, _, hw, hh = get_virtual_screen_bounds()
        if tw <= 0 or th <= 0 or hw <= 0 or hh <= 0:
            return None
        if scale is None:
            scale = min(hw / tw, hh / th)
            scale = min(scale, 1.0)
        if scale <= 0:
            return None
        new_w = max(1, int(tw * scale))
        new_h = max(1, int(th * scale))
        if new_w <= 0 or new_h <= 0:
            return None
        if self._region and (new_w > hw or new_h > hh):
            return None
        if new_w == tw and new_h == th:
            resized = img
        else:
            resized = img.resize((new_w, new_h), Image.LANCZOS)
        haystack, off_x, off_y = self._grab_haystack()
        if haystack is None:
            return None
        return self._locate_in_haystack(resized, haystack, off_x, off_y, confidence=confidence)

    def _wait_for_image(self, path, timeout=None, confidence=None, scale=None):
        if timeout is None:
            deadline = None
        else:
            deadline = time.time() + max(0.0, timeout)
        while not self._stop.is_set():
            box = self._locate_image(path, confidence=confidence, scale=scale)
            if box:
                return box
            if deadline is not None and time.time() >= deadline:
                return None
            time.sleep(0.2)
        return None

    def _wait_for_any_image(self, paths, timeout=None, confidence=None, scale=None):
        if timeout is None:
            deadline = None
        else:
            deadline = time.time() + max(0.0, timeout)
        while not self._stop.is_set():
            for p in paths:
                box = self._locate_image(p, confidence=confidence, scale=scale)
                if box:
                    return p, box
            if deadline is not None and time.time() >= deadline:
                return None, None
            time.sleep(0.2)
        return None, None

    def execute(self, parsed, speed=1.0, repeat=1, on_finish=None):
        self.reset()
        label_map = {}
        for idx, (cmd, args) in enumerate(parsed):
            if cmd == 'LABEL' and args:
                label_map[args[0]] = idx
        try:
            for r in range(repeat):
                self._region = self._default_region
                self._last_found = False
                if self._stop.is_set():
                    break
                idx = 0
                while idx < len(parsed):
                    if self._stop.is_set():
                        break
                    cmd, args = parsed[idx]
                    if cmd == 'LABEL':
                        idx += 1
                        continue
                    if cmd == 'GOTO':
                        if args and args[0] in label_map:
                            idx = label_map[args[0]] + 1
                            continue
                        print('GOTO: label not found:', args[0] if args else '')
                        idx += 1
                        continue
                    if cmd == 'IF_FOUND':
                        if args and self._last_found and args[0] in label_map:
                            idx = label_map[args[0]] + 1
                            continue
                        idx += 1
                        continue
                    if cmd == 'IF_NOT_FOUND':
                        if args and (not self._last_found) and args[0] in label_map:
                            idx = label_map[args[0]] + 1
                            continue
                        idx += 1
                        continue
                    if cmd == 'REGION':
                        if len(args) >= 4:
                            try:
                                x = int(args[0]); y = int(args[1])
                                w = int(args[2]); h = int(args[3])
                                self._region = (x, y, w, h)
                            except Exception:
                                self._region = None
                        else:
                            self._region = None
                    if cmd == 'WAIT':
                        if not args:
                            idx += 1
                            continue
                        tval = ScriptParser.parse_wait_token(args[0])
                        target = (tval / speed) if speed > 0 else tval
                        slept = 0.0
                        slice_len = 0.05
                        while slept < target and not self._stop.is_set():
                            time.sleep(min(slice_len, target - slept))
                            slept += slice_len
                    elif cmd == 'CLICK':
                        btn = args[0] if args else 'left'
                        if len(args) >= 3:
                            try:
                                x, y = int(args[1]), int(args[2])
                                if pyautogui:
                                    pyautogui.click(x, y, button=btn)
                            except Exception as e:
                                print('Click error:', e)
                        else:
                            try:
                                if pyautogui:
                                    pyautogui.click(button=btn)
                            except Exception as e:
                                print('Click error:', e)
                    elif cmd == 'KEY_DOWN':
                        key_raw = ' '.join(args)
                        key_to_press = self._normalize_key(key_raw)
                        try:
                            if pyautogui:
                                pyautogui.keyDown(key_to_press)
                        except Exception as e:
                            print('keyDown error:', e)
                    elif cmd == 'KEY_UP':
                        key_raw = ' '.join(args)
                        key_to_press = self._normalize_key(key_raw)
                        try:
                            if pyautogui:
                                pyautogui.keyUp(key_to_press)
                        except Exception as e:
                            print('keyUp error:', e)
                    elif cmd == 'IMG_WAIT':
                        path, _paths, timeout, confidence, _, scale = self._parse_img_args(args)
                        if not path:
                            idx += 1
                            continue
                        box = self._wait_for_image(path, timeout=timeout, confidence=confidence, scale=scale)
                        self._last_found = bool(box)
                        if not box:
                            print('IMG_WAIT: not found:', path)
                    elif cmd == 'IMG_CLICK':
                        path, _paths, timeout, confidence, button, scale = self._parse_img_args(args)
                        if not path:
                            idx += 1
                            continue
                        box = self._wait_for_image(path, timeout=timeout, confidence=confidence, scale=scale)
                        self._last_found = bool(box)
                        if box and pyautogui:
                            cx = int(box.left + box.width / 2)
                            cy = int(box.top + box.height / 2)
                            try:
                                pyautogui.click(cx, cy, button=button)
                            except Exception as e:
                                print('IMG_CLICK error:', e)
                        elif not box:
                            print('IMG_CLICK: not found:', path)
                    elif cmd == 'IMG_CLICK_ANY':
                        _path, paths, timeout, confidence, button, scale = self._parse_img_args(args)
                        if not paths:
                            idx += 1
                            continue
                        found_path, box = self._wait_for_any_image(paths, timeout=timeout, confidence=confidence, scale=scale)
                        self._last_found = bool(box)
                        if box and pyautogui:
                            cx = int(box.left + box.width / 2)
                            cy = int(box.top + box.height / 2)
                            try:
                                pyautogui.click(cx, cy, button=button)
                            except Exception as e:
                                print('IMG_CLICK_ANY error:', e)
                        elif not box:
                            print('IMG_CLICK_ANY: not found')
                    else:
                        print('Unknown command:', cmd)
                    idx += 1
        finally:
            if callable(on_finish):
                try:
                    on_finish()
                except Exception:
                    pass

class MacroApp:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title('Macro Recorder')
        self.root.geometry('777x600')

        self.store = EventStore()
        self.recorder = Recorder(self.store)
        self.executor = Executor()
        self.image_path = None
        self.search_region = None
        self.image_var = tk.StringVar(value='Image: (none)')
        self.region_var = tk.StringVar(value='Region: full screen')

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('Primary.TButton', foreground='#ffffff', background='#2563eb', padding=6)
        style.map('Primary.TButton', background=[('active', '#1d4ed8')])
        style.configure('Record.TButton', foreground='#ffffff', background='#ef4444', padding=6)
        style.map('Record.TButton', background=[('active', '#dc2626')])
        style.configure('Stop.TButton', foreground='#ffffff', background='#f59e0b', padding=6)
        style.map('Stop.TButton', background=[('active', '#d97706')])
        style.configure('Neutral.TButton', foreground='#111827', background='#e5e7eb', padding=6)
        style.map('Neutral.TButton', background=[('active', '#d1d5db')])
        style.configure('Tool.TButton', foreground='#ffffff', background='#10b981', padding=6)
        style.map('Tool.TButton', background=[('active', '#059669')])
        style.configure('Insert.TButton', foreground='#ffffff', background='#6366f1', padding=6)
        style.map('Insert.TButton', background=[('active', '#4f46e5')])

        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=(8, 4))

        rec_frame = ttk.LabelFrame(top, text='Recording')
        rec_frame.pack(side=tk.LEFT, padx=4)
        self.btn_record = ttk.Button(rec_frame, text='Record', command=self.start_recording, style='Record.TButton')
        self.btn_record.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_stop = ttk.Button(rec_frame, text='Stop', command=self.stop_recording, style='Stop.TButton')
        self.btn_stop.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_stop.state(['disabled'])

        play_frame = ttk.LabelFrame(top, text='Playback')
        play_frame.pack(side=tk.LEFT, padx=4)
        self.btn_play = ttk.Button(play_frame, text='Play', command=self.play, style='Primary.TButton')
        self.btn_play.pack(side=tk.LEFT, padx=4, pady=4)

        file_frame = ttk.LabelFrame(top, text='Files')
        file_frame.pack(side=tk.LEFT, padx=4)
        self.btn_save = ttk.Button(file_frame, text='Save', command=self.save, style='Neutral.TButton')
        self.btn_save.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_load = ttk.Button(file_frame, text='Load', command=self.load, style='Neutral.TButton')
        self.btn_load.pack(side=tk.LEFT, padx=4, pady=4)

        tools_row = ttk.Frame(self.root)
        tools_row.pack(fill=tk.X, padx=8, pady=(0, 4))

        img_tools = ttk.LabelFrame(tools_row, text='Image')
        img_tools.pack(side=tk.LEFT, padx=4)
        self.btn_image = ttk.Button(img_tools, text='Image...', command=self.select_image, style='Tool.TButton')
        self.btn_image.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_capture = ttk.Button(img_tools, text='Capture...', command=self.capture_image, style='Tool.TButton')
        self.btn_capture.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_region = ttk.Button(img_tools, text='Region...', command=self.select_region, style='Tool.TButton')
        self.btn_region.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_region_clear = ttk.Button(img_tools, text='Clear Region', command=self.clear_region, style='Tool.TButton')
        self.btn_region_clear.pack(side=tk.LEFT, padx=4, pady=4)

        insert_tools = ttk.LabelFrame(tools_row, text='Insert')
        insert_tools.pack(side=tk.LEFT, padx=4)
        self.btn_insert_region = ttk.Button(insert_tools, text='Insert REGION', command=self.insert_region, style='Insert.TButton')
        self.btn_insert_region.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_img_click = ttk.Button(insert_tools, text='Insert IMG_CLICK', command=self.insert_img_click, style='Insert.TButton')
        self.btn_img_click.pack(side=tk.LEFT, padx=4, pady=4)
        self.btn_img_click_any = ttk.Button(insert_tools, text='Insert IMG_CLICK_ANY', command=self.insert_img_click_any, style='Insert.TButton')
        self.btn_img_click_any.pack(side=tk.LEFT, padx=4, pady=4)

        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        self.lbl_image = ttk.Label(info_frame, textvariable=self.image_var)
        self.lbl_image.pack(side=tk.LEFT, padx=4)
        self.lbl_region = ttk.Label(info_frame, textvariable=self.region_var)
        self.lbl_region.pack(side=tk.LEFT, padx=12)

        text_frame = ttk.Frame(self.root)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.txt = tk.Text(text_frame, wrap=tk.NONE, font=('Consolas', 11))
        self.txt.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        hbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.txt.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt.configure(xscrollcommand=hbar.set)

        self.status_var = tk.StringVar(value='Ready.')
        status = ttk.Label(self.root, textvariable=self.status_var)
        status.pack(fill=tk.X, padx=4, pady=(0, 4))

    def set_status(self, text):
        try:
            self.status_var.set(text)
        except Exception:
            pass

    def text_get(self):
        return self.txt.get('1.0', tk.END).rstrip('\n')

    def text_set(self, s):
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, s)

    def start_recording(self):
        txt = self.text_get()
        if not txt.strip():
            self.store.clear()
            self.set_status('Starting recording (cleared events).')
        else:
            current_from_events = ScriptParser.events_to_script(self.store.snapshot()).strip()
            if current_from_events != txt.strip():
                parsed = ScriptParser.parse(txt)
                evs = ScriptParser.script_to_events(parsed)
                self.store.clear(); self.store.extend(evs)
                self.set_status('Starting recording: synced events to text (will append).')
            else:
                self.set_status('Starting recording (appending to events).')
        try:
            self.recorder.start()
            self.btn_record.state(['disabled'])
            self.btn_stop.state(['!disabled'])
        except Exception as e:
            messagebox.showerror('Error', f'Could not start recorder: {e}')

    def stop_recording(self):
        self.recorder.stop()
        self.btn_record.state(['!disabled'])
        self.btn_stop.state(['disabled'])
        self.text_set(ScriptParser.events_to_script(self.store.snapshot()))
        self.set_status(f'Stopped. Events recorded: {len(self.store)}')

    def play(self):
        txt = self.text_get()
        parsed = ScriptParser.parse(txt)
        if not parsed:
            messagebox.showinfo('Play', 'Script vazio. Grave ou carregue um script primeiro.')
            return
        speed = simple_dialog_float('Velocidade', 'Velocidade (1.0 = normal):', default=1.0)
        if speed is None:
            return
        repeat = simple_dialog_int('Repetições', 'Quantas repetições (inteiro >=1):', default=1)
        if repeat is None or repeat < 1:
            messagebox.showerror('Erro', 'Repetições inválidas')
            return
        self.set_status(f'Playing at {speed}x, {repeat} times... (ESC to stop)')
        self.executor.set_default_region(self.search_region)

        def on_finish():
            self.root.after(0, lambda: self.set_status('Done playing or stopped.'))

        def run():
            if keyboard is not None:
                def on_stop(k):
                    try:
                        if k == keyboard.Key.esc:
                            self.executor.stop()
                            return False
                    except Exception:
                        pass
                with keyboard.Listener(on_press=on_stop):
                    self.executor.execute(parsed, speed=speed, repeat=repeat, on_finish=on_finish)
            else:
                self.executor.execute(parsed, speed=speed, repeat=repeat, on_finish=on_finish)

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def save(self):
        txt = self.text_get()
        if not txt.strip():
            messagebox.showinfo('Save', 'Nada para salvar.')
            return
        fname = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text Files', '*.txt')])
        if not fname:
            return
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(txt)
        self.set_status(f'Saved to {fname}')

    def load(self):
        fname = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt'), ('All files', '*.*')])
        if not fname:
            return
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
        self.text_set(content)
        parsed = ScriptParser.parse(content)
        evs = ScriptParser.script_to_events(parsed)
        self.store.clear(); self.store.extend(evs)
        self.set_status(f'Loaded {fname} (events synced)')

    def refresh(self):
        self.text_set(ScriptParser.events_to_script(self.store.snapshot()))
        self.set_status('Script refreshed from recorded events')

    def _next_capture_path(self):
        base_dir = os.path.join(os.getcwd(), 'captures')
        os.makedirs(base_dir, exist_ok=True)
        stamp = time.strftime('%Y%m%d_%H%M%S')
        for idx in range(1, 1000):
            name = f'capture_{stamp}_{idx:03d}.png'
            path = os.path.join(base_dir, name)
            if not os.path.exists(path):
                return path
        return os.path.join(base_dir, f'capture_{stamp}_{int(time.time() * 1000) % 1000:03d}.png')

    def capture_image(self):
        if not pyautogui and mss is None:
            messagebox.showerror('Image', 'pyautogui or mss is required for screenshots.')
            return
        self.root.withdraw()
        self.root.update_idletasks()
        try:
            region = select_screen_region(self.root)
        finally:
            self.root.deiconify()
        if not region:
            self.set_status('Capture cancelled.')
            return
        try:
            if mss is not None:
                from PIL import Image
                with mss.mss() as sct:
                    mon = {'left': region[0], 'top': region[1],
                           'width': region[2], 'height': region[3]}
                    img = sct.grab(mon)
                    shot = Image.frombytes('RGB', img.size, img.rgb)
            else:
                shot = pyautogui.screenshot(region=region)
        except Exception as e:
            messagebox.showerror('Image', f'Could not capture screenshot: {e}')
            return
        path = self._next_capture_path()
        try:
            shot.save(path)
        except Exception as e:
            messagebox.showerror('Image', f'Could not save image: {e}')
            return
        self.image_path = path
        self.image_var.set(f'Image: {path}')
        self.set_status(f'Captured image saved to {path}')

    def select_image(self):
        fname = filedialog.askopenfilename(
            filetypes=[('Image Files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')]
        )
        if not fname:
            return
        self.image_path = fname
        self.image_var.set(f'Image: {fname}')

    def select_region(self):
        region = select_screen_region(self.root)
        if region:
            self.search_region = region
            x, y, w, h = region
            self.region_var.set(f'Region: x={x} y={y} w={w} h={h}')
            self.executor.set_default_region(region)
        else:
            self.set_status('Region selection cancelled.')

    def clear_region(self):
        self.search_region = None
        self.region_var.set('Region: full screen')
        self.executor.set_default_region(None)

    def insert_region(self):
        if not self.search_region:
            messagebox.showinfo('Region', 'Select a region first.')
            return
        x, y, w, h = self.search_region
        line = f"REGION {x} {y} {w} {h}"
        self.txt.insert(tk.INSERT, line + '\n')

    def _insert_img_command(self, cmd):
        if not self.image_path:
            messagebox.showinfo('Image', 'Select an image first.')
            return
        lines = []
        if self.search_region:
            x, y, w, h = self.search_region
            lines.append(f"REGION {x} {y} {w} {h}")
        lines.append(f"{cmd} {_quote_arg(self.image_path)}")
        self.txt.insert(tk.INSERT, "\n".join(lines) + '\n')

    def insert_img_wait(self):
        self._insert_img_command('IMG_WAIT')

    def insert_img_click(self):
        self._insert_img_command('IMG_CLICK')

    def insert_img_click_any(self):
        extra = filedialog.askopenfilenames(
            title='Select images',
            filetypes=[('Image Files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'), ('All files', '*.*')]
        )
        if extra:
            paths = list(extra)
        elif self.image_path:
            paths = [self.image_path]
        else:
            messagebox.showinfo('Image', 'Select or capture at least one image first.')
            return
        lines = []
        if self.search_region:
            x, y, w, h = self.search_region
            lines.append(f"REGION {x} {y} {w} {h}")
        parts = " ".join(_quote_arg(p) for p in paths)
        lines.append(f"IMG_CLICK_ANY {parts}")
        self.txt.insert(tk.INSERT, "\n".join(lines) + '\n')

def simple_dialog_float(title, prompt, default=1.0):
    try:
        import tkinter.simpledialog as sd
        res = sd.askstring(title, prompt, initialvalue=str(default))
        if res is None:
            return None
        return float(res)
    except Exception:
        return None

def simple_dialog_int(title, prompt, default=1):
    try:
        import tkinter.simpledialog as sd
        res = sd.askstring(title, prompt, initialvalue=str(default))
        if res is None:
            return None
        return int(res)
    except Exception:
        return None

def main():
    app = MacroApp()
    app.set_status('Ready.')
    app.root.protocol('WM_DELETE_WINDOW', lambda: app.root.destroy())
    app.root.mainloop()

if __name__ == '__main__':
    main()
