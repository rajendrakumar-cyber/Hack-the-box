import capstone

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

# register_initializer_func is at 0x66c0
offset = 0x66c0
code = data[offset:offset + 0x300]

print("Disassembling register_initializer_func at 0x66c0...")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for i in md.disasm(code, offset):
    print(f"0x{i.address:x}: {i.mnemonic} {i.op_str}")
