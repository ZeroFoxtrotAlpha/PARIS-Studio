import os, sys, math, struct, subprocess, tempfile, shutil

try:
    from pydub import AudioSegment
    HAVE_PYDUB = True
except Exception:
    HAVE_PYDUB = False

from utils import which

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
                b += struct.pack('<h', int(32767 * s))
                tp += 1
        else:
            b += b'\x00\x00' * n; tp += n
    return bytes(b), tp

def write_wav(p, pcm, sr=44100):
    import wave
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm)

def play_wav(path):
    try:
        if sys.platform.startswith("win"):
            import winsound; winsound.PlaySound(path, winsound.SND_FILENAME)
        elif sys.platform == "darwin" and which("afplay"):
            subprocess.run(["afplay", path])
        elif which("aplay"):
            subprocess.run(["aplay", path])
    except:
        pass

def export_mp3(rows, freq, sr, vol, ramp, outpath):
    if not HAVE_PYDUB:
        raise RuntimeError("Install pydub + ffmpeg for MP3 export.")
    tmp = tempfile.mkdtemp(prefix="morse_")
    wav = os.path.join(tmp, "tmp.wav")
    pcm, _ = synth(rows, freq, sr, vol, ramp)
    write_wav(wav, pcm, sr)
    AudioSegment.from_wav(wav).export(outpath, format="mp3")
    shutil.rmtree(tmp, ignore_errors=True)
