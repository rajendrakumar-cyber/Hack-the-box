import capstone

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

offset = 0x3720
code = data[offset:offset + 0x30]

print("Disassembling start of render_reward_step at 0x3720...")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for i in md.disasm(code, offset):
    print(f"0x{i.address:x}: {i.mnemonic} {i.op_str}")
