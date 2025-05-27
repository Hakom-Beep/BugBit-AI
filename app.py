import streamlit as st
import re
from bug_detector import scan_kode, auto_fix

# --- Fungsi dari script detektor bug kamu (ringkas dan sesuaikan) ---
def cek_infinite_loop(code):
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if 'while True:' in line:
            next_lines = lines[i+1:i+6]
            if not any("break" in l for l in next_lines):
                return True
    return False

def cek_if_tanpa_blok(code):
    lines = code.split('\n')
    for i in range(len(lines)-1):
        if re.match(r"\bif\s+[^\n]+:\s*$", lines[i]):
            if i+1 == len(lines) or not lines[i+1].startswith(' '):
                return True
    return False

def cari_variabel_tanpa_deklarasi(code):
    declared = set()
    masalah = []
    lines = code.split("\n")

    for i, line in enumerate(lines):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            match = re.match(r"^(\w+)\s*=", line)
            if match:
                declared.add(match.group(1))
        tokens = re.findall(r"\b([a-zA-Z_]\w*)\b", line)
        for token in tokens:
            if (
                token not in declared and
                token not in dir(__builtins__) and
                token not in {"if", "while", "for", "def", "return", "break", "and", "or", "True", "False", "None"}
            ):
                msg = f"Variabel '{token}' di baris {i+1} belum dideklarasikan"
                solusi = f"Tambahkan deklarasi variabel terlebih dahulu, misalnya: {token} = ..."
                masalah.append((msg, solusi))

    return masalah

def cek_fungsi_tak_dikenal(code):
    defined = set(re.findall(r"def\s+(\w+)\(", code))
    called = set(re.findall(r"(\w+)\(", code))
    builtin = {"print", "range", "len", "input", "str", "int", "float"}

    masalah = []
    for fn in called:
        if fn not in defined and fn not in builtin:
            msg = f"Fungsi '{fn}' dipanggil tapi tidak ada definisinya"
            solusi = f"Pastikan fungsi sudah didefinisikan, misalnya: def {fn}(): ..."
            masalah.append((msg, solusi))
    return masalah

def scan_kode(code):
    bugs = []

    if cek_infinite_loop(code):
        bugs.append(("Loop 'while True' tanpa 'break' ditemukan", "Tambahkan 'break' di dalam loop"))

    if cek_if_tanpa_blok(code):
        bugs.append(("If statement tanpa blok ditemukan", "Tambahkan indentasi atau blok kode setelah if"))

    if "print(" in code:
        bugs.append(("print() terdeteksi (mungkin debug)", "Gunakan logging atau hapus jika tidak perlu"))

    bugs.extend(cari_variabel_tanpa_deklarasi(code))
    bugs.extend(cek_fungsi_tak_dikenal(code))

    return bugs

def auto_fix_infinite_loop(code):
    lines = code.split('\n')
    fixed = False
    for i, line in enumerate(lines):
        if 'while True:' in line and not any("break" in l for l in lines[i+1:i+6]):
            lines.insert(i+1, '    break')
            fixed = True
    return '\n'.join(lines), fixed

def auto_fix_if_tanpa_blok(code):
    lines = code.split('\n')
    fixed = False
    for i in range(len(lines)-1):
        if re.match(r"\bif\s+[^\n]+:\s*$", lines[i]) and (i+1 == len(lines) or not lines[i+1].startswith(' ')):
            lines.insert(i+1, '    pass')
            fixed = True
    return '\n'.join(lines), fixed

def auto_fix_undeclared_vars(code):
    declared = set()
    used = set()
    lines = code.split("\n")

    for line in lines:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            match = re.match(r"^(\w+)\s*=", line)
            if match:
                declared.add(match.group(1))
        tokens = re.findall(r"\b([a-zA-Z_]\w*)\b", line)
        for token in tokens:
            if token not in dir(__builtins__) and not line.startswith("def "):
                used.add(token)

    undeclared = used - declared - {"if", "while", "for", "def", "return", "break", "and", "or", "True", "False", "None"}
    fix_lines = [f"{var} = None" for var in undeclared]
    return '\n'.join(fix_lines) + '\n' + code if undeclared else code, bool(undeclared)

def auto_fix_fungsi_tak_dikenal(code):
    defined = set(re.findall(r"def\s+(\w+)\(", code))
    called = set(re.findall(r"(\w+)\(", code))
    builtin = {"print", "range", "len", "input", "str", "int", "float"}

    unknown_funcs = [fn for fn in called if fn not in defined and fn not in builtin]
    fixes = [f"def {fn}():\n    pass" for fn in unknown_funcs]
    return code + '\n\n' + '\n\n'.join(fixes) if unknown_funcs else code, bool(unknown_funcs)

def auto_fix(code):
    code, fix1 = auto_fix_infinite_loop(code)
    code, fix2 = auto_fix_if_tanpa_blok(code)
    code, fix3 = auto_fix_undeclared_vars(code)
    code, fix4 = auto_fix_fungsi_tak_dikenal(code)

    return code, any([fix1, fix2, fix3, fix4])

# ----------------------------------------------------------

st.set_page_config(page_title="BugBit AI", page_icon="🪲", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: #121212;
        color: #E0E0E0;
        font-family: 'Poppins', sans-serif;
    }
    .header {
        font-size: 48px;
        font-weight: 700;
        color: #1E90FF;
        text-align: center;
        margin-bottom: 10px;
    }
    .subheader {
        font-size: 24px;
        color: #8A2BE2;
        text-align: center;
        margin-bottom: 40px;
    }
    .upload-area {
        border: 3px dashed #1E90FF;
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        transition: border-color 0.3s;
    }
    .upload-area:hover {
        border-color: #8A2BE2;
    }
    .bug-report {
        background-color: #222;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">BugBit AI — Detect Bugs Before They Bite!</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Automated Python Bug Detection Powered by AI. Upload your Python code (.py) below.</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload your Python (.py) file here", type=["py"])

if uploaded_file:
    # Baca isi file
    kode = uploaded_file.read().decode("utf-8")

    st.markdown('<div class="upload-area">Analyzing your Python code, please wait...</div>', unsafe_allow_html=True)

    bugs = scan_kode(kode)
    if bugs:
        st.markdown('<div class="bug-report"><b>🐞 Bug ditemukan:</b></div>', unsafe_allow_html=True)
        for i, (msg, sol) in enumerate(bugs, 1):
            st.markdown(f"{i}. {msg}\n   Solusi: {sol}")

        if st.button("Terapkan Perbaikan Otomatis"):
            kode_baru, fixed = auto_fix(kode)
            if fixed:
                st.markdown('<div class="bug-report"><b>🛠️ Perbaikan otomatis telah diterapkan. Berikut kode hasil perbaikan:</b></div>', unsafe_allow_html=True)
                st.code(kode_baru, language='python')
            else:
                st.markdown("✅ Tidak ada perbaikan otomatis yang diperlukan.")
    else:
        st.markdown("✅ Tidak ditemukan bug pada kode.")

st.markdown("<hr style='border-color:#333;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#555;'>© 2025 BugBit AI | All rights reserved.</p>", unsafe_allow_html=True)
