from utils import dot_ms

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

def build_rows(text, wpm, letsp_ms, wordsp_ms):
    d_dot = dot_ms(wpm)
    d_dash = 3 * d_dot
    d_intra = d_dot
    d_ich = letsp_ms
    d_iw = wordsp_ms
    rows = []
    for wi, w in enumerate(text.strip().split()):
        for ci, ch in enumerate(w):
            code = MORSE.get(ch.upper())
            if not code: continue
            for ei, e in enumerate(code):
                rows.append((int(d_dot if e == '.' else d_dash), 1))
                if ei < len(code) - 1:
                    rows.append((int(d_intra), 0))
            if ci < len(w) - 1:
                rows.append((int(d_ich), 0))
        if wi < len(text.split()) - 1:
            rows.append((int(d_iw), 0))
    return rows
