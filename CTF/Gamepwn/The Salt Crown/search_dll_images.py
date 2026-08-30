# Search for image headers in decrypted_memory.bin

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

signatures = {
    b"\x89PNG\r\n\x1a\n": "PNG Image",
    b"\xff\xd8\xff": "JPEG Image",
    b"RIFF": "RIFF (WEBP/WAV)",
}

found = False
for i in range(len(data) - 8):
    for sig, name in signatures.items():
        if data[i:i+len(sig)] == sig:
            print(f"Found {name} in DLL at offset {hex(i)}!")
            found = True

if not found:
    print("No images found in GDExtension DLL.")
