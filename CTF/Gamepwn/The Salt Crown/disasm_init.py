import capstone

# Load decrypted memory
with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

# challenge_core_library_init address is at 0x69a0
init_offset = 0x69a0
code = data[init_offset:init_offset + 0x200]

print("Disassembling challenge_core_library_init at 0x69a0...")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for i in md.disasm(code, init_offset):
    print(f"0x{i.address:x}: {i.mnemonic} {i.op_str}")
