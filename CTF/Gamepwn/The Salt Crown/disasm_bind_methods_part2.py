import capstone

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

offset = 0x1f16
code = data[offset:offset + 0x400]

print("Disassembling at 0x1f16...")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for i in md.disasm(code, offset):
    print(f"0x{i.address:x}: {i.mnemonic} {i.op_str}")
