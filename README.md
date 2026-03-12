# Macro Recorder

Simple macro recorder/player with image matching and multi-monitor support.

## Setup

```bash
python -m venv venv
pip install -r requirements.txt
python main.py
```

## UI Overview

- Record / Stop: capture mouse clicks and key events.
- Play: execute the script in the editor.
- Image...: choose a template image to match.
- Capture...: select an area and save a PNG under `captures/`.
- Region...: select the search region for image matching.
- Insert buttons: insert commands into the script.

## Script Commands

Basic:
- `WAIT <ms|s>`
- `CLICK <button> <x> <y>`
- `KEY_DOWN <key>`
- `KEY_UP <key>`

Image and region:
- `REGION x y w h`
- `IMG_WAIT <path> [timeout=] [confidence=] [scale=]`
- `IMG_CLICK <path> [timeout=] [confidence=] [scale=] [button=]`
- `IMG_CLICK_ANY <path1> <path2> ... [timeout=] [confidence=] [scale=] [button=]`

Flow control:
- `LABEL <name>`
- `GOTO <name>`
- `IF_FOUND <name>`
- `IF_NOT_FOUND <name>`

## Notes

- `confidence` requires `opencv-python`.
- `scale` helps when the template size differs from what is on screen.
- If a path contains backslashes, use quotes or prefer forward slashes.
- The `captures/` folder is ignored by git.
- Commands not linked to buttons: `IMG_WAIT`, `LABEL`, `GOTO`, `IF_FOUND`, `IF_NOT_FOUND`.
