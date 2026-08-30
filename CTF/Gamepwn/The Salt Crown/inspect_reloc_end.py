with open("The Salt Crown.exe", "rb") as f:
    f.seek(69429180)
    data = f.read(128)

print("Hex representation:")
print(data.hex())

print("\nReadable ASCII:")
ascii_chars = "".join(chr(b) if 32 <= b < 127 else "." for b in data)
print(ascii_chars)
