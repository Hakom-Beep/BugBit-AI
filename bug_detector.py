import os
import re

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

    if any([fix1, fix2, fix3, fix4]):
        print("🛠️ Perbaikan otomatis dilakukan.")
    else:
        print("✅ Tidak ada perbaikan yang diperlukan.")
    return code

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

def scan_kode(code, nama_file="(tidak diketahui)"):
    bugs = []

    if cek_infinite_loop(code):
        bugs.append(("Loop 'while True' tanpa 'break' ditemukan", "Tambahkan 'break' di dalam loop"))

    if cek_if_tanpa_blok(code):
        bugs.append(("If statement tanpa blok ditemukan", "Tambahkan indentasi atau blok kode setelah if"))

    if "print(" in code:
        bugs.append(("print() terdeteksi (mungkin debug)", "Gunakan logging atau hapus jika tidak perlu"))

    bugs.extend(cari_variabel_tanpa_deklarasi(code))
    bugs.extend(cek_fungsi_tak_dikenal(code))

    # Pastikan return dalam format list of tuples (pesan, solusi)
    hasil = []
    for item in bugs:
        if isinstance(item, str):
            hasil.append((item, ""))
        elif isinstance(item, tuple):
            hasil.append(item)
    return hasil

if __name__ == "__main__":
    path = input("Masukkan path file atau folder .py: ").strip()

    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            isi = f.read()

        bugs = scan_kode(isi, nama_file=os.path.basename(path))
        if bugs:
            print(f"\n🐞 Bug ditemukan di file {os.path.basename(path)}:")
            for i, (msg, sol) in enumerate(bugs, 1):
                print(f"{i}. {msg}\n   Solusi: {sol}\n")
        else:
            print("✅ Tidak ditemukan bug di kode.")

        perbaikan = input("Ingin terapkan perbaikan otomatis? (y/n): ").strip().lower()
        if perbaikan == "y":
            fixed_code = auto_fix(isi)
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            print("✅ Kode telah diperbaiki otomatis dan disimpan kembali.")

    elif os.path.isdir(path):
        files = [f for f in os.listdir(path) if f.endswith(".py")]
        for f in files:
            full = os.path.join(path, f)
            with open(full, "r", encoding="utf-8") as file:
                isi = file.read()

            bugs = scan_kode(isi, nama_file=f)
            if bugs:
                print(f"\n🐞 Bug ditemukan di file '{f}':")
                for i, (msg, sol) in enumerate(bugs, 1):
                    print(f"{i}. {msg}\n   Solusi: {sol}\n")
            else:
                print(f"✅ Tidak ditemukan bug di file '{f}'.")

            perbaikan = input(f"Ingin perbaiki otomatis file '{f}'? (y/n): ").strip().lower()
            if perbaikan == "y":
                fixed_code = auto_fix(isi)
                with open(full, "w", encoding="utf-8") as file:
                    file.write(fixed_code)
                print(f"✅ File '{f}' sudah diperbaiki dan disimpan.\n")
    else:
        print("❌ Path tidak valid.")
