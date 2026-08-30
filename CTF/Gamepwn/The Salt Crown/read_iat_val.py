import struct

with open("decrypted_memory.bin", "rb") as f:
    f.seek(0x7303c)
    val = f.read(8)

print(f"Value at 0x7303c (hex): {val.hex()}")
if len(val) == 8:
    print(f"Unpacked (uint64): {hex(struct.unpack('<Q', val)[0])}")
