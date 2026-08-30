import struct

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

image_base = 0x180000000
target_addr = 0x18007303c

print("Searching for references to BCryptDecrypt...")
found = False

# Search for RIP-relative references (ff 15 / ff 25 / 48 8b / 4c 8d etc.)
for i in range(len(data) - 6):
    # Check for call/jmp [rip + offset] -> ff 15 xx xx xx xx or ff 25 xx xx xx xx
    if data[i] == 0xff and data[i+1] in (0x15, 0x25):
        offset = struct.unpack("<i", data[i+2:i+6])[0]
        addr = image_base + i
        next_addr = addr + 6
        target = next_addr + offset
        if target == target_addr:
            instr_type = "call" if data[i+1] == 0x15 else "jmp"
            print(f"Found {instr_type} at offset {hex(i)} (Vaddr: {hex(addr)}) pointing to BCryptDecrypt!")
            found = True
            
    # Check for mov reg, [rip + offset] -> 48 8b xx xx xx xx
    elif data[i] == 0x48 and data[i+1] == 0x8b and (data[i+2] & 0xc7) == 0x05:
        # ModR/M byte: 0x05, 0x0d, 0x15, 0x1d, 0x25, 0x2d, 0x35, 0x3d
        offset = struct.unpack("<i", data[i+3:i+7])[0]
        addr = image_base + i
        next_addr = addr + 7
        target = next_addr + offset
        if target == target_addr:
            reg = (data[i+2] >> 3) & 7
            print(f"Found mov reg{reg} at offset {hex(i)} (Vaddr: {hex(addr)}) pointing to BCryptDecrypt!")
            found = True

if not found:
    print("No direct RIP-relative references found. Let's do a general scan for the address 0x18007303c.")
    for i in range(len(data) - 8):
        val = struct.unpack("<Q", data[i:i+8])[0]
        if val == target_addr:
            print(f"Found absolute address 0x18007303c at offset {hex(i)} (Vaddr: {hex(image_base + i)})")
