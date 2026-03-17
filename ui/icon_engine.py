import os
from PIL import Image, ImageEnhance, ImageOps, ImageTk
import customtkinter as ctk


DEFAULT_ICON_MAP = {
    "record": (0, 0),
    "stop": (1, 0),
    "play": (2, 0),
    "step": (3, 0),
    "continue": (4, 0),
    "folder": (5, 0),
    "save": (0, 1),
    "load": (1, 1),
    "image": (2, 1),
    "capture": (3, 1),
    "region": (4, 1),
    "clear": (5, 1),
    "insert": (0, 2),
    "properties": (1, 2),
    "preview": (2, 2),
    "breakpoint": (3, 2),
    "console": (4, 2),
    "theme": (5, 2),
}

DEFAULT_FILE_MAP = {
    "record": "Record.png",
    "stop": "Stop.png",
    "play": "Play.png",
    "step": "Step Execution.png",
    "continue": "Play.png",
    "folder": "Open Folder.png",
    "save": "Save.png",
    "load": "Load.png",
    "image": "Image Search.png",
    "capture": "Capture Screen.png",
    "region": "Image Search.png",
    "clear": "Clear Region.png",
    "insert": "Settings.png",
    "properties": "Settings.png",
    "preview": "Image Search.png",
    "breakpoint": "Breakpoint.png",
    "console": "Settings.png",
    "theme": "Settings.png",
}


class IconEngine:
    def __init__(self, sprite_path=None, columns=6, rows=3, offset_x=0, offset_y=0, icon_dir=None, icon_files=None):
        self.sprite_path = sprite_path
        self.columns = columns
        self.rows = rows
        self.offset_x = offset_x
        self.offset_y = offset_y
        self._sprite = None
        if sprite_path and os.path.exists(sprite_path):
            self._sprite = Image.open(sprite_path).convert("RGBA")
            self._cell_w = self._sprite.width / float(columns)
            self._cell_h = self._sprite.height / float(rows)
            self._registry = dict(DEFAULT_ICON_MAP)
        else:
            self._cell_w = 0
            self._cell_h = 0
            self._registry = {}
        self._icon_dir = icon_dir
        self._file_map = dict(DEFAULT_FILE_MAP)
        if icon_files:
            self._file_map.update(icon_files)
        self._crop_cache = {}
        self._resize_cache = {}
        self._tint_cache = {}
        self._photo_cache = {}

    def register(self, name, col, row):
        self._registry[name] = (col, row)

    def set_offset(self, offset_x=0, offset_y=0):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self._crop_cache.clear()
        self._resize_cache.clear()
        self._tint_cache.clear()
        self._photo_cache.clear()

    def get_icon(self, name, size, state="normal", theme=None, brightness=None):
        key = self._key(name, size, state, theme, brightness, kind="ctk")
        if key in self._tint_cache:
            return self._tint_cache[key]
        img = self._get_variant(name, size, state, theme, brightness)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        self._tint_cache[key] = ctk_img
        return ctk_img

    def get_photo(self, name, size, state="normal", theme=None, brightness=None):
        key = self._key(name, size, state, theme, brightness, kind="photo")
        if key in self._photo_cache:
            return self._photo_cache[key]
        img = self._get_variant(name, size, state, theme, brightness)
        photo = ImageTk.PhotoImage(img)
        self._photo_cache[key] = photo
        return photo

    def _key(self, name, size, state, theme, brightness, kind):
        accent = (theme or {}).get("accent", "")
        tint = (theme or {}).get("icon_tint", "")
        b = round(brightness, 2) if brightness is not None else None
        return (kind, name, size, state, accent, tint, b)

    def _get_variant(self, name, size, state, theme, brightness):
        base = self._get_resized(name, size)
        img = base.copy()
        img = self._apply_state(img, state, theme, brightness)
        return img

    def _get_resized(self, name, size):
        key = (name, size)
        if key in self._resize_cache:
            return self._resize_cache[key]
        base = self._get_crop(name)
        bw, bh = base.size
        if bw > size or bh > size:
            resized = ImageOps.contain(base, (size, size), Image.LANCZOS)
        else:
            resized = base.copy()
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        x = max(0, (size - resized.width) // 2)
        y = max(0, (size - resized.height) // 2)
        canvas.paste(resized, (x, y), resized)
        resized = canvas
        self._resize_cache[key] = resized
        return resized

    def _get_crop(self, name):
        if name in self._crop_cache:
            return self._crop_cache[name]
        if self._sprite is not None:
            if name not in self._registry:
                raise KeyError(f"Icon '{name}' not registered.")
            col, row = self._registry[name]
            x0 = int(self.offset_x + col * self._cell_w)
            y0 = int(self.offset_y + row * self._cell_h)
            x1 = int(self.offset_x + (col + 1) * self._cell_w)
            y1 = int(self.offset_y + (row + 1) * self._cell_h)
            crop = self._sprite.crop((x0, y0, x1, y1))
        else:
            if not self._icon_dir:
                raise FileNotFoundError("Icon directory not configured.")
            file_name = self._file_map.get(name, "Settings.png")
            path = os.path.join(self._icon_dir, file_name)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Icon file not found: {path}")
            crop = Image.open(path).convert("RGBA")
        self._crop_cache[name] = crop
        return crop

    def _apply_state(self, img, state, theme, brightness):
        theme = theme or {}
        base_alpha = img.split()[-1]
        if brightness is not None:
            img = self._apply_brightness(img, brightness)
        if state == "hover":
            img = self._apply_brightness(img, 1.1)
        if state == "active":
            img = self._apply_tint(img, theme.get("accent", "#3b82f6"))
        if state == "disabled":
            img = self._apply_disabled(img)
        tint = theme.get("icon_tint")
        if tint and state == "normal":
            img = self._apply_tint(img, tint, strength=0.15)
        if state == "disabled":
            base_alpha = base_alpha.point(lambda p: int(p * 0.4))
        img.putalpha(base_alpha)
        return img

    def _apply_brightness(self, img, factor):
        rgb = img.convert("RGB")
        alpha = img.split()[-1]
        rgb = ImageEnhance.Brightness(rgb).enhance(factor)
        rgb.putalpha(alpha)
        return rgb

    def _apply_tint(self, img, color, strength=0.35):
        alpha = img.split()[-1]
        overlay = Image.new("RGBA", img.size, color)
        blended = Image.blend(img, overlay, strength)
        blended.putalpha(alpha)
        return blended

    def _apply_disabled(self, img):
        alpha = img.split()[-1]
        gray = ImageOps.grayscale(img.convert("RGB")).convert("RGBA")
        gray.putalpha(alpha)
        return gray
