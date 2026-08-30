import pefile

pe = pefile.PE("The Salt Crown.exe")

# Find the last section on disk
last_section = max(pe.sections, key=lambda s: s.PointerToRawData)

pck_start = last_section.PointerToRawData + last_section.SizeOfRawData

print(f"Last section: {last_section.Name.decode().strip()}")
print(f"PointerToRawData: {last_section.PointerToRawData}")
print(f"SizeOfRawData: {last_section.SizeOfRawData}")
print(f"Inferred PCK Start Offset: {pck_start}")

# Let's read the first 16 bytes at this offset
with open("The Salt Crown.exe", "rb") as f:
    f.seek(pck_start)
    first_bytes = f.read(16)
print(f"Bytes at offset {pck_start}: {first_bytes.hex()} ({first_bytes})")
