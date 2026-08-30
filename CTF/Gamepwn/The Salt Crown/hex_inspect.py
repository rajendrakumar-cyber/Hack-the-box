with open("game.pck", "rb") as f:
    header = f.read(128)

print("Hex representation of start of game.pck:")
print(header.hex())

# Print readable characters
print("\nReadable ASCII:")
ascii_chars = "".join(chr(b) if 32 <= b < 127 else "." for b in header)
print(ascii_chars)
