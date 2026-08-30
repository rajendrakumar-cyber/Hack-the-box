import pefile
from unicorn import *
from unicorn.x86_const import *

# Load PE file
pe = pefile.PE("challenge_core.windows.template_release.x86_64.dll")

# Initialize Unicorn emulator in X86_64 mode
mu = Uc(UC_ARCH_X86, UC_MODE_64)

# Determine memory layout
image_base = pe.OPTIONAL_HEADER.ImageBase  # 0x180000000
size_of_image = pe.OPTIONAL_HEADER.SizeOfImage # 0x74000

# Map memory for DLL image (aligned to page size)
mu.mem_map(image_base, size_of_image)

# Write PE headers to memory
mu.mem_write(image_base, pe.header)

# Write PE sections to memory
for section in pe.sections:
    vaddr = image_base + section.VirtualAddress
    size = section.Misc_VirtualSize
    data = section.get_data()
    # Write raw data
    mu.mem_write(vaddr, data)
    # If virtual size is larger than raw data size, pad with zeroes
    if size > len(data):
        mu.mem_write(vaddr + len(data), b'\x00' * (size - len(data)))

# Map memory for stack
stack_base = 0x90000000
stack_size = 0x100000 # 1MB
mu.mem_map(stack_base, stack_size)
# Set RSP to the end of stack (aligned)
mu.reg_write(UC_X86_REG_RSP, stack_base + stack_size - 0x1000)

# Set registers for DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved)
mu.reg_write(UC_X86_REG_RCX, image_base)
mu.reg_write(UC_X86_REG_RDX, 1) # DLL_PROCESS_ATTACH
mu.reg_write(UC_X86_REG_R8, 0)

# Target start address and stop address
entry_point = image_base + pe.OPTIONAL_HEADER.AddressOfEntryPoint # 0x180072220
stop_address = image_base + 0x723bf # 0x1800723bf

print(f"Starting emulation from 0x{entry_point:x} to 0x{stop_address:x}...")
try:
    mu.emu_start(entry_point, stop_address)
    print("Emulation finished successfully!")
except Exception as e:
    print(f"Emulation failed: {e}")
    # Print current registers
    rip = mu.reg_read(UC_X86_REG_RIP)
    print(f"RIP: 0x{rip:x}")

# Read the entire decrypted memory of the image
decrypted_memory = mu.mem_read(image_base, size_of_image)

# Save the decrypted memory to a file
with open("decrypted_memory.bin", "wb") as f:
    f.write(decrypted_memory)
print("Decrypted memory saved to decrypted_memory.bin!")

