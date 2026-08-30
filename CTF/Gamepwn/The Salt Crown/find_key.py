import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_REG_RIP, X86_OP_MEM
import math

# Load the PE file
pe = pefile.PE("The Salt Crown.exe")

# Locate .text, .rdata, and .data sections
text_sec = None
rdata_sec = None
data_sec = None

for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name == ".text":
        text_sec = sec
    elif name == ".rdata":
        rdata_sec = sec
    elif name == ".data":
        data_sec = sec

if not text_sec:
    print("Could not find .text section")
    exit(1)

# Helper to calculate entropy
def entropy(data):
    if not data:
        return 0.0
    entropy = 0
    for x in range(256):
        p_x = data.count(x) / len(data)
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy

# Map virtual address to file offset
def get_data_by_vaddr(vaddr, size):
    for sec in pe.sections:
        start = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
        end = start + sec.Misc_VirtualSize
        if vaddr >= start and vaddr + size <= end:
            offset = sec.PointerToRawData + (vaddr - start)
            return pe.__data__[offset:offset+size]
    return None

# Disassemble .text section and look for LEA
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

image_base = pe.OPTIONAL_HEADER.ImageBase
text_data = text_sec.get_data()
text_vaddr = image_base + text_sec.VirtualAddress

print("Disassembling .text section (this might take a minute)...")
candidates = set()

# Process in chunks to avoid capstone memory issues or speed it up
chunk_size = 1000000
for offset in range(0, len(text_data), chunk_size):
    chunk = text_data[offset:offset+chunk_size]
    curr_vaddr = text_vaddr + offset
    
    for inst in md.disasm(chunk, curr_vaddr):
        if inst.mnemonic == "lea" and len(inst.operands) == 2:
            op1 = inst.operands[1]
            if op1.type == X86_OP_MEM and op1.value.mem.base == X86_REG_RIP:
                # Target address = RIP of next instruction + displacement
                next_ip = inst.address + inst.size
                target_vaddr = next_ip + op1.value.mem.disp
                
                # Check if target is in .rdata or .data
                # .rdata range
                if rdata_sec:
                    rdata_start = image_base + rdata_sec.VirtualAddress
                    rdata_end = rdata_start + rdata_sec.Misc_VirtualSize
                    if rdata_start <= target_vaddr < rdata_end:
                        candidates.add(target_vaddr)
                # .data range
                if data_sec:
                    data_start = image_base + data_sec.VirtualAddress
                    data_end = data_start + data_sec.Misc_VirtualSize
                    if data_start <= target_vaddr < data_end:
                        candidates.add(target_vaddr)

print(f"Found {len(candidates)} candidate addresses. Extracting keys...")

valid_keys = []
for vaddr in candidates:
    key_bytes = get_data_by_vaddr(vaddr, 32)
    if key_bytes and len(key_bytes) == 32:
        # Check entropy and null byte count
        nulls = key_bytes.count(0)
        ent = entropy(key_bytes)
        # AES keys usually have high entropy and very few nulls
        if nulls <= 2 and ent > 4.0:
            valid_keys.append((vaddr, key_bytes, ent))

# Sort by entropy descending
valid_keys.sort(key=lambda x: x[2], reverse=True)

for vaddr, key, ent in valid_keys[:20]:
    print(f"Address: {hex(vaddr)}, Entropy: {ent:.4f}, Hex: {key.hex()}")
