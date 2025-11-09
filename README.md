# PARIS-Studio (aislop)

A standalone Morse code generator, visualizer, and player — built in Python with Tkinter and zero external dependencies (except optional MP3 export via pydub + ffmpeg).

This tool lets you type text, see real-time Morse timing, and play or export the signal in multiple formats.
It automatically updates the preview, effective WPM, and timing graph as you type or adjust any parameters.

✨ Features

🧭 Live updates: Automatically recalculates timing, spacing, and visual graph when text or parameters change — no refresh button needed.

🔉 Audio playback: Generates a pure tone from your current Morse sequence using the built-in system audio player:

Windows → winsound

macOS → afplay

Linux → aplay or paplay

⚙️ Timing visualization: Displays a bar graph showing key-down (ON) and key-up (OFF) durations scaled by your selected WPM, Farnsworth, and spacing parameters.

🧾 Detailed preview: Shows the .paris (CSV-style) output with duration/value pairs, plus full header info.

💾 Export options:

.paris format (CSV timing file)

.wav (uncompressed audio)

.mp3 (optional, via pydub + ffmpeg)

🔧 Parameter controls:

Character speed (WPM)

Farnsworth speed (effective WPM)

Dot:Dash weight ratio

Jitter (random timing variation %)

Letter spacing (dot units)

Word spacing (dot units)

Pre/post delays (milliseconds)

Tone frequency, volume, sample rate, and keying ramp

📦 Requirements

Base requirements:

Python 3.8+

Tkinter (included in standard Python)

Optional for MP3 export:

pip install pydub
# ffmpeg also required, install via:
# Windows: https://ffmpeg.org/download.html
# Linux/macOS: sudo apt install ffmpeg  OR  brew install ffmpeg

▶️ Usage
1. Run the program
python morse_generator_player.py

2. Enter your text

Type any text in the main “Text” box (e.g., CQ CQ TEST DE N0CALL).

3. Adjust timing parameters

Modify:

Character WPM → Base Morse element speed

Farnsworth WPM → Slower overall spacing for training

Weight → Dot-to-dash ratio (default 1:3)

Letter/Word spacing → Adjust intra-word and inter-word gaps

Jitter → Add natural irregularity

4. View real-time updates

The Effective WPM label updates instantly.

The Graph below shows ON/OFF keying segments (bars = tone ON).

The Preview pane shows the generated .paris content.

5. Play audio

Press Play to hear the current Morse sequence using your system audio player.

6. Export files

Export .paris — Save timing data for replay or external encoding.

Export WAV — Save the tone sequence as a standard audio file.

Export MP3 — Requires pydub and ffmpeg (see above).

🧠 Technical Overview

Each Morse signal is composed of time-coded ON/OFF segments based on:

Element	Duration	Default multiple
Dot (·)	1 dot unit	1
Dash (–)	3 dot units	weight × 1
Intra-character space	1 dot unit	fixed
Inter-character space	3 dot units	scaled by Farnsworth
Word space	7 dot units	scaled by Farnsworth
Pre/Post delay	User-specified	milliseconds

The .paris format used for export is a CSV-like timing file with this structure:

# Word: PARIS
# Character speed: 15 WPM
# Farnsworth spacing: 5 WPM
# Effective total speed: 6.00 WPM
duration_ms,value
84,1
84,0
252,1
...


value = 1 means key-down (tone ON), value = 0 means key-up (silence).

🧩 Example Output

Example:
Text: "PARIS"
Character WPM: 15
Farnsworth: 5
Weight: 3.0

Preview:

# Word: PARIS
# Char speed: 15 WPM
# Farnsworth: 5 WPM
# Effective WPM: 6.00
duration_ms,value
84,1
84,0
252,1
84,0
252,1
84,0
84,1
504,0
...


Graph:
Black rectangles = tone ON
White gaps = silence

🎚️ Audio Parameters
Parameter	Default	Description
Tone frequency	700 Hz	Sine wave pitch
Volume	0.6	0–1 linear gain
Sample rate	44100 Hz	Audio precision
Ramp (ms)	5	Soft fade-in/out to prevent clicks
⚖️ License

MIT License
(c) 2025 ChatGPT + Contributors

You may freely use, modify, and distribute this software with attribution.

💬 Summary

This tool provides a complete end-to-end Morse practice and synthesis environment — from timing visualization to audio generation — designed for hams, learners, and developers who want to experiment with precise Morse timing or export data for keying systems.
