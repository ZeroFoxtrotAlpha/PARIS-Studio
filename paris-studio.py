#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-Page Morse Generator + Player
- Auto-updating graph and preview (no Preview button)
- Type text or change parameters → updates instantly
- Live WPM, graph, and playback
- Export .paris / .wav / .mp3 (optional)
"""

import os, sys, math, struct, tempfile, shutil, subprocess, threading, random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from pydub import AudioSegment
    HAVE_PYDUB = True
except Exception:
    HAVE_PYDUB = False

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
}

def clamp(v, lo, hi): return max(lo, min(hi, v))
def dot_ms(wpm): return 1200.0 / max(wpm, 1e-9)
def apply_jitter(d, pct): return d if pct <= 0 else d * (1 + random.uniform(-pct/100, pct/100))
def which(cmd): return shutil.which(cmd) is not None

def build_rows(text, char_wpm, farns_wpm, weight, jitter, pre, post, letsp, wordsp):
    char_wpm = clamp(char_wpm, 1, 80)
    farns_wpm = clamp(farns_wpm, 1, char_wpm)
    d_dot = dot_ms(char_wpm); d_f = dot_ms(farns_wpm)
    d_dash = weight * d_dot
    d_intra = d_dot
    d_ich = letsp * d_f
    d_iw = wordsp * d_f
    rows = []
    if pre: rows.append((int(pre), 0))
    for wi, w in enumerate(text.strip().split()):
        for ci, ch in enumerate(w):
            code = MORSE.get(ch.upper())
            if not code: continue
            for ei, e in enumerate(code):
                rows.append((int(apply_jitter(d_dot if e == "." else d_dash, jitter)), 1))
                if ei < len(code) - 1: rows.append((int(apply_jitter(d_intra, jitter)), 0))
            if ci < len(w) - 1: rows.append((int(apply_jitter(d_ich, jitter)), 0))
        if wi < len(text.split()) - 1: rows.append((int(apply_jitter(d_iw, jitter)), 0))
    if post: rows.append((int(post), 0))
    return rows

def estimate_eff(char, farns, weight, letsp, wordsp):
    if char <= 0 or farns <= 0: return 0
    d = dot_ms(char); f = dot_ms(farns)
    avg = (d + f) / 2; space = ((letsp / 3) + (wordsp / 7)) / 2
    tot = 50 * avg * space
    return (60000 * 50) / tot if tot > 0 else char

def synth(rows, freq=700, sr=44100, vol=0.5, ramp=5):
    ramp_s = int(sr * (ramp / 1000))
    b = bytearray(); tp = 0
    for dur, val in rows:
        n = int(sr * (dur / 1000))
        if val:
            for i in range(n):
                if ramp_s > 0:
                    if i < ramp_s:
                        env = 0.5 * (1 - math.cos(math.pi * i / ramp_s))
                    elif n - i <= ramp_s:
                        env = 0.5 * (1 - math.cos(math.pi * (n - i) / ramp_s))
                    else:
                        env = 1
                else:
                    env = 1
                s = vol * env * math.sin(2 * math.pi * freq * tp / sr)
                b += struct.pack('<h', int(32767 * max(-1, min(1, s))))
                tp += 1
        else:
            b += b'\x00\x00' * n; tp += n
    return bytes(b), tp

def write_wav(p, pcm, sr=44100):
    import wave
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Morse Generator + Player")
        self.geometry("950x750")
        self.tmp = None
        self.make_ui()
        self.update_preview()

    def make_ui(self):
        f = ttk.Frame(self, padding=10); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Text:").grid(row=0, column=0, sticky="w")
        self.txt = tk.Text(f, height=4, wrap="word")
        self.txt.grid(row=1, column=0, columnspan=8, sticky="nsew")
        self.txt.insert("1.0", "PARIS")
        self.txt.bind("<<Modified>>", lambda e: (self.txt.edit_modified(0), self.update_preview()))

        labels = ["Char WPM", "Farnsworth", "Weight", "Jitter", "Letter space", "Word space", "Pre-delay", "Post-delay"]
        defaults = ["15", "5", "3", "0", "3", "7", "0", "0"]
        self.vars = []
        for i, (n, v) in enumerate(zip(labels, defaults)):
            ttk.Label(f, text=n + ":").grid(row=2 + i // 4, column=(i % 4) * 2, sticky="w")
            sv = tk.StringVar(value=v)
            ttk.Entry(f, textvariable=sv, width=8).grid(row=2 + i // 4, column=(i % 4) * 2 + 1, sticky="w")
            sv.trace_add("write", lambda *a: self.update_preview())
            self.vars.append(sv)

        ttk.Label(f, text="Tone:").grid(row=4, column=0, sticky="w")
        self.freq = tk.StringVar(value="700")
        ttk.Entry(f, textvariable=self.freq, width=8).grid(row=4, column=1, sticky="w")
        ttk.Label(f, text="Vol(0-1):").grid(row=4, column=2, sticky="w")
        self.vol = tk.StringVar(value="0.6")
        ttk.Entry(f, textvariable=self.vol, width=8).grid(row=4, column=3, sticky="w")
        ttk.Label(f, text="SR:").grid(row=4, column=4, sticky="w")
        self.sr = tk.StringVar(value="44100")
        ttk.Entry(f, textvariable=self.sr, width=8).grid(row=4, column=5, sticky="w")
        ttk.Label(f, text="Ramp(ms):").grid(row=4, column=6, sticky="w")
        self.ramp = tk.StringVar(value="5")
        ttk.Entry(f, textvariable=self.ramp, width=8).grid(row=4, column=7, sticky="w")

        self.lbl = ttk.Label(f, text="Effective WPM: --", font=("Segoe UI", 10, "bold"))
        self.lbl.grid(row=5, column=0, columnspan=8, sticky="w", pady=4)

        ttk.Label(f, text="Timing Graph:").grid(row=6, column=0, columnspan=8, sticky="w")
        self.can = tk.Canvas(f, height=90, bg="white", bd=1, relief="sunken")
        self.can.grid(row=7, column=0, columnspan=8, sticky="ew", pady=5)

        b = ttk.Frame(f); b.grid(row=8, column=0, columnspan=8, sticky="w", pady=5)
        ttk.Button(b, text="Play", command=self.play_now).pack(side="left", padx=4)
        ttk.Button(b, text="Export .paris", command=self.save_paris).pack(side="left", padx=4)
        ttk.Button(b, text="Export WAV", command=self.save_wav).pack(side="left", padx=4)
        ttk.Button(b, text="Export MP3", command=self.save_mp3).pack(side="left", padx=4)

        ttk.Label(f, text="Preview:").grid(row=9, column=0, columnspan=8, sticky="w")
        self.out = tk.Text(f, height=16, wrap="none"); self.out.grid(row=10, column=0, columnspan=8, sticky="nsew")
        f.rowconfigure(10, weight=1)
        for c in range(8): f.columnconfigure(c, weight=1 if c % 2 else 0)
        self.bind("<Configure>", lambda e: self.redraw_graph())

    def parse(self):
        vals = []
        for v in self.vars:
            try: vals.append(float(v.get()))
            except: vals.append(0)
        return vals

    def build_preview(self):
        vals = self.parse()
        if len(vals) < 8: return [], ""
        char, farns, w, j, l, wsp, pre, post = vals
        txt = self.txt.get("1.0", "end").strip() or "PARIS"
        rows = build_rows(txt, char, farns, w, j, pre, post, l, wsp)
        eff = estimate_eff(char, farns, w, l, wsp)
        head = [
            f"# Word: {txt}",
            f"# Char speed: {char} WPM",
            f"# Farnsworth: {farns} WPM",
            f"# Effective WPM: {eff:.2f}",
            "duration_ms,value",
        ]
        return rows, "\n".join(head + [f"{d},{v}" for d, v in rows])

    def update_preview(self, *a):
        rows, txt = self.build_preview()
        self.out.delete("1.0", "end")
        self.out.insert("1.0", txt[:5000])
        eff_line = next((l for l in txt.splitlines() if "Effective WPM" in l), None)
        if eff_line: self.lbl.config(text=eff_line)
        self.rows_cache = rows
        self.redraw_graph()

    def redraw_graph(self):
        self.can.delete("all")
        rows = getattr(self, "rows_cache", [])
        if not rows: return
        w = self.can.winfo_width()
        total = sum(d for d, _ in rows)
        if total <= 0: return
        scale = w / total
        x = 0
        self.can.create_line(0, 80, w, 80, fill="gray")
        for d, v in rows:
            ww = max(1, int(d * scale))
            if v:
                self.can.create_rectangle(x, 20, x + ww, 70, fill="black", outline="")
            x += ww

    def play_now(self):
        rows, _ = self.build_preview()
        if not rows: return
        try:
            f = float(self.freq.get()); sr = int(self.sr.get()); v = float(self.vol.get()); r = float(self.ramp.get())
        except: return
        if self.tmp: shutil.rmtree(self.tmp, ignore_errors=True)
        self.tmp = tempfile.mkdtemp(prefix="morse_")
        wav = os.path.join(self.tmp, "preview.wav")
        pcm, _ = synth(rows, f, sr, v, r); write_wav(wav, pcm, sr)
        threading.Thread(target=self._play, args=(wav,), daemon=True).start()

    def _play(self, wav):
        try:
            if sys.platform.startswith("win"):
                import winsound; winsound.PlaySound(wav, winsound.SND_FILENAME)
            elif sys.platform == "darwin" and which("afplay"):
                subprocess.run(["afplay", wav])
            elif which("aplay"):
                subprocess.run(["aplay", wav])
        except: pass

    def save_paris(self):
        rows, txt = self.build_preview()
        if not rows: return
        path = filedialog.asksaveasfilename(defaultextension=".paris", filetypes=[("PARIS", "*.paris")])
        if not path: return
        with open(path, "w", encoding="utf-8") as f: f.write(txt)
        messagebox.showinfo("Saved", f"Saved {path}")

    def save_wav(self):
        rows, _ = self.build_preview()
        if not rows: return
        try:
            f = float(self.freq.get()); sr = int(self.sr.get()); v = float(self.vol.get()); r = float(self.ramp.get())
        except: return
        out = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if not out: return
        pcm, _ = synth(rows, f, sr, v, r); write_wav(out, pcm, sr)
        messagebox.showinfo("Saved", f"WAV saved:\n{out}")

    def save_mp3(self):
        if not HAVE_PYDUB:
            messagebox.showwarning("MP3 not available", "Install pydub+ffmpeg for MP3 export.")
            return
        rows, _ = self.build_preview()
        if not rows: return
        try:
            f = float(self.freq.get()); sr = int(self.sr.get()); v = float(self.vol.get()); r = float(self.ramp.get())
        except: return
        out = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
        if not out: return
        tmp = tempfile.mkdtemp(prefix="morse_")
        wav = os.path.join(tmp, "t.wav")
        pcm, _ = synth(rows, f, sr, v, r); write_wav(wav, pcm, sr)
        AudioSegment.from_wav(wav).export(out, format="mp3")
        shutil.rmtree(tmp, ignore_errors=True)
        messagebox.showinfo("Saved", f"MP3 saved:\n{out}")

if __name__ == "__main__":
    App().mainloop()
