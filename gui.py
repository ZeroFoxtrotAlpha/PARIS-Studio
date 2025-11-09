import os, tempfile, threading, shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from morse import build_rows
from audio import synth, write_wav, play_wav, export_mp3

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KF5JEX Paris Studio")
        self.geometry("900x720")
        self.tmp = None
        self.playing = False
        self.make_ui()
        self.update_preview()

    def make_ui(self):
        f = ttk.Frame(self, padding=10); f.pack(fill="both", expand=True)
        ttk.Label(f, text="Text:").grid(row=0, column=0, sticky="w")
        self.txt = tk.Text(f, height=4, wrap="word")
        self.txt.grid(row=1, column=0, columnspan=6, sticky="nsew")
        self.txt.insert("1.0", "PARIS")
        self.txt.bind("<<Modified>>", lambda e: (self.txt.edit_modified(0), self.update_preview()))

        ttk.Label(f, text="Char WPM:").grid(row=2, column=0, sticky="w")
        self.wpm = tk.StringVar(value="15")
        ttk.Entry(f, textvariable=self.wpm, width=8).grid(row=2, column=1, sticky="w")
        self.wpm.trace_add("write", lambda *a: self.update_preview())

        ttk.Label(f, text="Letter space (ms):").grid(row=2, column=2, sticky="w")
        self.lspace = tk.StringVar(value="300")
        ttk.Entry(f, textvariable=self.lspace, width=8).grid(row=2, column=3, sticky="w")
        self.lspace.trace_add("write", lambda *a: self.update_preview())

        ttk.Label(f, text="Word space (ms):").grid(row=2, column=4, sticky="w")
        self.wspace = tk.StringVar(value="700")
        ttk.Entry(f, textvariable=self.wspace, width=8).grid(row=2, column=5, sticky="w")
        self.wspace.trace_add("write", lambda *a: self.update_preview())

        ttk.Label(f, text="Tone:").grid(row=3, column=0, sticky="w")
        self.freq = tk.StringVar(value="700")
        ttk.Entry(f, textvariable=self.freq, width=8).grid(row=3, column=1, sticky="w")
        ttk.Label(f, text="Vol(0-1):").grid(row=3, column=2, sticky="w")
        self.vol = tk.StringVar(value="0.6")
        ttk.Entry(f, textvariable=self.vol, width=8).grid(row=3, column=3, sticky="w")
        ttk.Label(f, text="SR:").grid(row=3, column=4, sticky="w")
        self.sr = tk.StringVar(value="44100")
        ttk.Entry(f, textvariable=self.sr, width=8).grid(row=3, column=5, sticky="w")

        ttk.Label(f, text="Ramp(ms):").grid(row=4, column=0, sticky="w")
        self.ramp = tk.StringVar(value="5")
        ttk.Entry(f, textvariable=self.ramp, width=8).grid(row=4, column=1, sticky="w")

        ttk.Label(f, text="Timing Graph:").grid(row=5, column=0, columnspan=6, sticky="w")
        self.can = tk.Canvas(f, height=90, bg="white", bd=1, relief="sunken")
        self.can.grid(row=6, column=0, columnspan=6, sticky="ew", pady=5)

        self.play_button = ttk.Button(f, text="Start", command=self.toggle_play)
        self.play_button.grid(row=7, column=0, sticky="w", pady=5)
        ttk.Button(f, text="Import .paris", command=self.load_paris).grid(row=7, column=1, sticky="w")
        ttk.Button(f, text="Export .paris", command=self.save_paris).grid(row=7, column=2, sticky="w")
        ttk.Button(f, text="Export WAV", command=self.save_wav).grid(row=7, column=3, sticky="w")
        ttk.Button(f, text="Export MP3", command=self.save_mp3).grid(row=7, column=4, sticky="w")

        ttk.Label(f, text="Preview:").grid(row=8, column=0, columnspan=6, sticky="w")
        self.out = tk.Text(f, height=16, wrap="none")
        self.out.grid(row=9, column=0, columnspan=6, sticky="nsew")

        f.rowconfigure(9, weight=1)
        for c in range(6): f.columnconfigure(c, weight=1 if c % 2 else 0)
        self.bind("<Configure>", lambda e: self.redraw_graph())

    def toggle_play(self):
        if self.playing:
            self.playing = False
            self.play_button.config(text="Start")
        else:
            self.playing = True
            self.play_button.config(text="Stop")
            threading.Thread(target=self.play_now, daemon=True).start()

    def play_now(self):
        rows, _ = self.build_preview()
        if not rows:
            self.playing = False; self.play_button.config(text="Start"); return
        try:
            f = float(self.freq.get()); sr = int(self.sr.get())
            v = float(self.vol.get()); r = float(self.ramp.get())
        except:
            self.playing = False; self.play_button.config(text="Start"); return

        if self.tmp: shutil.rmtree(self.tmp, ignore_errors=True)
        self.tmp = tempfile.mkdtemp(prefix="morse_")
        wav = os.path.join(self.tmp, "preview.wav")
        pcm, _ = synth(rows, f, sr, v, r)
        write_wav(wav, pcm, sr)
        if self.playing:
            play_wav(wav)
        self.playing = False
        self.play_button.config(text="Start")

    def build_preview(self):
        try:
            wpm = float(self.wpm.get()); l = float(self.lspace.get()); w = float(self.wspace.get())
        except: return [], ""
        txt = self.txt.get("1.0", "end").strip() or "PARIS"
        rows = build_rows(txt, wpm, l, w)
        head = [f"# Word: {txt}", f"# Char speed: {wpm} WPM", f"# Letter space: {l} ms", f"# Word space: {w} ms", "duration_ms,value"]
        return rows, "\n".join(head + [f"{d},{v}" for d,v in rows])

    def update_preview(self, *a):
        rows, txt = self.build_preview()
        self.out.delete("1.0", "end"); self.out.insert("1.0", txt[:5000])
        self.rows_cache = rows; self.redraw_graph()

    def redraw_graph(self):
        self.can.delete("all"); rows = getattr(self, "rows_cache", [])
        if not rows: return
        w = self.can.winfo_width(); total = sum(d for d,_ in rows)
        if total <= 0: return
        scale = w / total; x = 0
        for d,v in rows:
            ww = max(1, int(d * scale))
            if v: self.can.create_rectangle(x, 20, x+ww, 70, fill="black", outline="")
            x += ww

    def save_paris(self):
        rows, txt = self.build_preview()
        if not rows: return
        path = filedialog.asksaveasfilename(defaultextension=".paris", filetypes=[("PARIS", "*.paris")])
        if not path: return
        with open(path, "w", encoding="utf-8") as f: f.write(txt)
        messagebox.showinfo("Saved", f"Saved {path}")

    def load_paris(self):
        path = filedialog.askopenfilename(filetypes=[("PARIS", "*.paris"), ("All files", "*.*")])
        if not path: return
        rows = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('duration'):
                        continue
                    try:
                        dur, val = line.split(',')
                        rows.append((int(float(dur)), int(float(val))))
                    except: pass
            if not rows:
                messagebox.showwarning("Empty file", "No timing data found."); return
            self.rows_cache = rows
            self.out.delete("1.0", "end"); self.out.insert("1.0", open(path).read()[:5000])
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def save_wav(self):
        rows, _ = self.build_preview()
        if not rows: return
        try:
            f = float(self.freq.get()); sr = int(self.sr.get())
            v = float(self.vol.get()); r = float(self.ramp.get())
        except: return
        out = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if not out: return
        pcm, _ = synth(rows, f, sr, v, r); write_wav(out, pcm, sr)
        messagebox.showinfo("Saved", f"WAV saved:\n{out}")

    def save_mp3(self):
        try:
            f = float(self.freq.get()); sr = int(self.sr.get())
            v = float(self.vol.get()); r = float(self.ramp.get())
        except: return
        out = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
        if not out: return
        try:
            export_mp3(self.rows_cache, f, sr, v, r, out)
            messagebox.showinfo("Saved", f"MP3 saved:\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
