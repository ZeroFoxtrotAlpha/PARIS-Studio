import shutil

def dot_ms(wpm):
    return 1200.0 / max(wpm, 1e-9)

def which(cmd):
    return shutil.which(cmd) is not None
