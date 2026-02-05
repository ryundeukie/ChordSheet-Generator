import streamlit as st
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# -----------------------------
# CONFIG
# -----------------------------
FONT_SIZE = 15
LINE_HEIGHT = 20
LEFT_MARGIN = 50
TOP_MARGIN = 750
CHAR_WIDTH = 7.2


CHORD_ORDER = ['C', 'C#', 'D', 'D#', 'E', 'F',
               'F#', 'G', 'G#', 'A', 'A#', 'B']

ENHARMONIC = {
    'Db': 'C#',
    'Eb': 'D#',
    'Gb': 'F#',
    'Ab': 'G#',
    'Bb': 'A#'
}

CHORD_REGEX = r'\b([A-G](#|b)?(m|maj7|sus4|sus2|dim|aug)?\d*)\b'

# -----------------------------
# CHORD UTILITIES
# -----------------------------
def normalize_chord(chord):
    root = re.match(r'[A-G](#|b)?', chord)
    if not root:
        return chord
    root = root.group()
    rest = chord[len(root):]

    root = ENHARMONIC.get(root, root)
    return root + rest


def transpose_chord(chord, steps):
    root_match = re.match(r'[A-G](#|b)?', chord)
    if not root_match:
        return chord

    root = normalize_chord(root_match.group())
    rest = chord[len(root_match.group()):]

    if root not in CHORD_ORDER:
        return chord

    idx = CHORD_ORDER.index(root)
    new_root = CHORD_ORDER[(idx + steps) % len(CHORD_ORDER)]
    return new_root + rest


def transpose_line(line, steps):
    def repl(match):
        return transpose_chord(match.group(0), steps)

    return re.sub(CHORD_REGEX, repl, line)

def draw_line_with_bold_chords(c, x, y, line):
    cursor_x = x
    last_idx = 0

    for match in re.finditer(CHORD_REGEX, line):
        start, end = match.span()

        # Draw normal text before chord
        normal_text = line[last_idx:start]
        c.setFont("Courier", FONT_SIZE)
        c.drawString(cursor_x, y, normal_text)
        cursor_x += len(normal_text) * CHAR_WIDTH

        # Draw chord in bold
        chord_text = line[start:end]
        c.setFont("Courier-Bold", FONT_SIZE)
        c.drawString(cursor_x, y, chord_text)
        cursor_x += len(chord_text) * CHAR_WIDTH

        last_idx = end

    # Draw remaining text
    remaining = line[last_idx:]
    c.setFont("Courier", FONT_SIZE)
    c.drawString(cursor_x, y, remaining)


# -----------------------------
# FORMAT SONG
# -----------------------------
def format_song(text, steps):
    output = []

    for line in text.splitlines():
        # Normalize tabs so spacing survives PDF rendering
        line = line.replace('\t', '    ')

        # Only transpose chords in-place
        if re.search(CHORD_REGEX, line):
            line = transpose_line(line, steps)

        # Preserve line EXACTLY
        output.append(line)

    return output



# -----------------------------
# PDF GENERATION
# -----------------------------
def generate_pdf(lines, title):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Courier", FONT_SIZE)

    y = TOP_MARGIN

    # Title
    c.setFont("Courier-Bold", FONT_SIZE + 2)
    c.drawString(LEFT_MARGIN, y, title)
    y -= LINE_HEIGHT * 2
    c.setFont("Courier", FONT_SIZE)

    for line in lines:
        if y < 50:
            c.showPage()
            c.setFont("Courier", FONT_SIZE)
            y = TOP_MARGIN

        draw_line_with_bold_chords(c, LEFT_MARGIN, y, line)
        y -= LINE_HEIGHT

    c.save()
    buffer.seek(0)
    return buffer


# -----------------------------
# STREAMLIT UI
# -----------------------------
st.set_page_config(page_title="Church Chord Sheet Maker Trial")

st.title("🎵 Church Chord Sheet Maker")

title = st.text_input("Song title", "Untitled Song")

st.text("Paste lyrics and chords below:")
song_text = st.text_area("", height=300)

key_change = st.radio(
    "Change key:",
    ["Lower", "Same", "Higher"],
    horizontal=True
)

KEY_SHIFT = {
    "Lower": -1,
    "Same": 0,
    "Higher": 1
}

if st.button("Generate Chord Sheet"):
    if not song_text.strip():
        st.warning("Please paste lyrics and chords.")
    else:
        formatted = format_song(song_text, KEY_SHIFT[key_change])

        st.subheader("Preview")
        st.code("\n".join(formatted))

        pdf = generate_pdf(formatted, title)

        st.download_button(
            label="📄 Download PDF",
            data=pdf,
            file_name=f"{title}.pdf",
            mime="application/pdf"
        )

        st.success("Done! Ready for rehearsal 🙌")
