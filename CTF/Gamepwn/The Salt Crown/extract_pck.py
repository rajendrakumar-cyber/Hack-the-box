with open("The Salt Crown.exe", "rb") as f:
    data = f.read()

# Let's write the PCK starting from offset 888600 (which is 0xd8f18)
pck_offset = 888600
pck_data = data[pck_offset:]

with open("game.pck", "wb") as f:
    f.write(pck_data)

print(f"Extracted game.pck starting from offset {pck_offset}!")
