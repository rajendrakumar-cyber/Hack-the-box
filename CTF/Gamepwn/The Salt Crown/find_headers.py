with open("The Salt Crown.exe", "rb") as f:
    f.seek(69431296)
    data = f.read()

signatures = {
    b"GDPC": "Godot Pack (GDPC)",
    b"GDEX": "Godot Encrypted Pack (GDEX)",
    b"SCX": "SCX",
    b"\x89PNG\r\n\x1a\n": "PNG Image",
    b"PK\x03\x04": "Zip Archive (PK)",
    b"OggS": "Ogg Audio",
    b"RIFF": "RIFF (WAV/WEBP)",
    b"\x37\x7a\xbc\xaf\x27\x1c": "7z Archive",
}

for i in range(len(data) - 8):
    for sig, name in signatures.items():
        if data[i:i+len(sig)] == sig:
            print(f"Found {name} at relative offset {hex(i)} (Vaddr: {hex(69431296 + i)})")
