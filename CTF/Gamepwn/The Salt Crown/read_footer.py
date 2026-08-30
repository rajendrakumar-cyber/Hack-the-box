with open("The Salt Crown.exe", "rb") as f:
    f.seek(-64, 2)
    footer = f.read()

print("Hex of last 64 bytes:")
print(footer.hex())

# Let's check the last 12 bytes specifically
if len(footer) >= 12:
    pck_magic = footer[-4:]
    # In Godot, the last 8 bytes are the offset (uint64)
    import struct
    pck_offset = struct.unpack("<Q", footer[-12:-4])[0]
    print(f"\nLast 12 bytes: offset = {pck_offset} (hex: {hex(pck_offset)}), magic = {pck_magic}")
