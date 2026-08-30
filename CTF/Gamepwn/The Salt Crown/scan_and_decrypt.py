import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_REG_RIP, X86_OP_MEM
from Cryptodome.Cipher import AES
import struct

# Load the PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

iv = pck_data[:16]
ciphertext = pck_data[16:]

# Locate sections
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

# Map virtual address to file offset
def get_data_by_vaddr(vaddr, size):
    for sec in pe.sections:
        start = pe.OPTIONAL_HEADER.ImageBase + sec.VirtualAddress
        end = start + sec.Misc_VirtualSize
        if vaddr >= start and vaddr + size <= end:
            offset = sec.PointerToRawData + (vaddr - start)
            return pe.__data__[offset:offset+size]
    return None

# Disassemble and collect all target addresses
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

image_base = pe.OPTIONAL_HEADER.ImageBase
text_data = text_sec.get_data()
text_vaddr = image_base + text_sec.VirtualAddress

print("Collecting LEA target addresses...")
candidates = set()

chunk_size = 1000000
for offset in range(0, len(text_data), chunk_size):
    chunk = text_data[offset:offset+chunk_size]
    curr_vaddr = text_vaddr + offset
    
    for inst in md.disasm(chunk, curr_vaddr):
        if inst.mnemonic == "lea" and len(inst.operands) == 2:
            op1 = inst.operands[1]
            if op1.type == X86_OP_MEM and op1.value.mem.base == X86_REG_RIP:
                next_ip = inst.address + inst.size
                target_vaddr = next_ip + op1.value.mem.disp
                
                # Check if target is in .rdata
                if rdata_sec:
                    rdata_start = image_base + rdata_sec.VirtualAddress
                    rdata_end = rdata_start + rdata_sec.Misc_VirtualSize
                    if rdata_start <= target_vaddr < rdata_end:
                        candidates.add(target_vaddr)
                # Check if target is in .data
                if data_sec:
                    data_start = image_base + data_sec.VirtualAddress
                    data_end = data_start + data_sec.Misc_VirtualSize
                    if data_start <= target_vaddr < data_end:
                        candidates.add(target_vaddr)

print(f"Found {len(candidates)} candidate addresses. Testing keys...")

found_key = None
# We will test both CFB (segment_size=128) and CBC just in case
for vaddr in candidates:
    key_bytes = get_data_by_vaddr(vaddr, 32)
    if not key_bytes or len(key_bytes) != 32:
        continue
        
    # Test CFB mode
    try:
        cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv, segment_size=128)
        dec = cipher.decrypt(ciphertext)
        if dec[40:44] == b"GDPC":
            found_key = (vaddr, key_bytes, "CFB")
            break
    except:
        pass
        
    # Test CBC mode
    try:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv=iv)
        dec = cipher.decrypt(ciphertext)
        if dec[40:44] == b"GDPC":
            found_key = (vaddr, key_bytes, "CBC")
            break
    except:
        pass

if found_key:
    vaddr, key_bytes, mode = found_key
    print(f"\nSUCCESS! Found key at Vaddr {hex(vaddr)} using {mode} mode.")
    print(f"Key (hex): {key_bytes.hex()}")
    
    # Let's decrypt the entire PCK file and write it to decrypted_game.pck
    print("Decrypting entire game.pck...")
    with open("game.pck", "rb") as f:
        full_data = f.read()
    
    full_iv = full_data[:16]
    full_ciphertext = full_data[16:]
    
    if mode == "CFB":
        cipher = AES.new(key_bytes, AES.MODE_CFB, iv=full_iv, segment_size=128)
    else:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv=full_iv)
        
    decrypted_full = cipher.decrypt(full_ciphertext)
    
    # Write only the real data (skipping the 40-byte header: length + hash)
    # The length of the decrypted pack data is given in the first 8 bytes
    pck_len = struct.unpack("<Q", decrypted_full[:8])[0]
    print(f"Pack data length: {pck_len} bytes")
    
    real_pck_data = decrypted_full[40:40+pck_len]
    
    with open("decrypted_game.pck", "wb") as f:
        f.write(real_pck_data)
    print("Saved decrypted pack to decrypted_game.pck!")
else:
    print("No valid key found among candidates.")
