# KF5JEX Paris Studio

A graphical Morse code generator and player with support for `.paris` timing files.

## Features
- Adjustable Character WPM, Letter spacing, Word spacing
- Manual Start/Stop playback (no autoplay)
- Live timing graph
- Import and export `.paris` files
- Export audio to `.wav` or `.mp3` (requires `pydub` + `ffmpeg`)

## Installation
```bash
pip install pydub
sudo apt install ffmpeg   # or brew install ffmpeg (macOS)
```

## Usage
Run the app:
```bash
python main.py
```

## File Structure
```
main.py         # Entry point
gui.py          # Tkinter UI
audio.py        # Audio synthesis & export
morse.py        # Morse timing generation
utils.py        # Helpers
```
