with open("The Salt Crown.exe", "rb") as f:
    data = f.read()

# Inferred PCK Start Offset is 69431296
real_pck_offset = 69431296
real_pck_data = data[real_pck_offset:]

with open("real_game.pck", "wb") as f:
    f.write(real_pck_data)

print(f"Extracted real_game.pck of size {len(real_pck_data)} bytes starting from offset {real_pck_offset}!")
