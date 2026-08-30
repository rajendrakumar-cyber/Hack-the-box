import struct

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

image_base = 0x180000000

print("Scanning for all calls/jmps to the IAT...")

# The IAT is from 0x180073000 to 0x180073100
iat_start = 0x180073000
iat_end = 0x180073100

for i in range(len(data) - 6):
    # Check RIP-relative call/jmp: ff 15 xx xx xx xx or ff 25 xx xx xx xx
    if data[i] == 0xff and data[i+1] in (0x15, 0x25):
        offset = struct.unpack("<i", data[i+2:i+6])[0]
        addr = image_base + i
        next_addr = addr + 6
        target = next_addr + offset
        
        if iat_start <= target < iat_end:
            instr = "call" if data[i+1] == 0x15 else "jmp"
            # Look up which import this is
            iat_offset = target - image_base
            print(f"Found {instr} at vaddr {hex(addr)} (offset {hex(i)}) targeting IAT slot {hex(target)}")
            
    # Check for mov reg, [rip + offset] where target is in IAT
    elif data[i] == 0x48 and data[i+1] == 0x8b and (data[i+2] & 0xc7) == 0x05:
        offset = struct.unpack("<i", data[i+3:i+7])[0]
        addr = image_base + i
        next_addr = addr + 7
        target = next_addr + offset
        if iat_start <= target < iat_end:
            reg = (data[i+2] >> 3) & 7
            print(f"Found mov reg{reg}, [IAT] at vaddr {hex(addr)} (offset {hex(i)}) targeting {hex(target)}")
