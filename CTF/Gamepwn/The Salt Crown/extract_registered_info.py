with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

offsets = {
    "offset_40788": 0x40788,
    "offset_4079c": 0x4079c,
    "offset_407a8": 0x407a8,
}

for name, off in offsets.items():
    s = []
    i = off
    while i < len(data) and data[i] != 0:
        s.append(chr(data[i]))
        i += 1
    print(f"{name} ({hex(off)}): {''.join(s)}")
