import pefile
from Cryptodome.Cipher import AES
import struct
import sys

# Load PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

iv = pck_data[:16]
ciphertext = pck_data[16:]

# Get .rdata and .data raw data
sections_data = []
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name in (".rdata", ".data"):
        print(f"Adding section {name} (size: {sec.SizeOfRawData} bytes)")
        sections_data.append((name, sec.get_data()))

print("Starting fast sliding-window scan...")
found = False

for name, sdata in sections_data:
    n_bytes = len(sdata)
    # Slide by 1 byte
    # To optimize Python speed, we do a quick check:
    # A random 32-byte AES key will rarely have more than 2 null bytes.
    # Also, we can test keys in blocks.
    print(f"Scanning section {name}...")
    
    # We can pre-extract all 32-byte slices
    # But to be memory-efficient and fast, let's do it in a loop
    for i in range(0, n_bytes - 32):
        # Quick check: if the candidate contains too many null bytes, skip
        candidate = sdata[i:i+32]
        
        # A quick filter to avoid setting up AES for obviously non-key data:
        # Most of .rdata is filled with string tables (lots of nulls) or padding.
        # AES keys have very few nulls.
        if candidate.count(0) > 1:
            continue
            
        # Try decrypting with CFB mode
        try:
            cipher = AES.new(candidate, AES.MODE_CFB, iv=iv, segment_size=128)
            dec = cipher.decrypt(ciphertext)
            if dec[40:44] == b"GDPC":
                print(f"\nFOUND KEY! Section: {name}, Offset: {hex(i)}")
                print(f"Key (hex): {candidate.hex()}")
                pck_len = struct.unpack("<Q", dec[:8])[0]
                print(f"Decrypted Pack Length: {pck_len}")
                
                # Decrypt the entire PCK and save it
                print("Decrypting entire game.pck...")
                with open("game.pck", "rb") as f:
                    full_data = f.read()
                
                full_iv = full_data[:16]
                full_ciphertext = full_data[16:]
                
                cipher = AES.new(candidate, AES.MODE_CFB, iv=full_iv, segment_size=128)
                decrypted_full = cipher.decrypt(full_ciphertext)
                real_pck_data = decrypted_full[40:40+pck_len]
                
                with open("decrypted_game.pck", "wb") as out_f:
                    out_f.write(real_pck_data)
                print("Saved decrypted pack to decrypted_game.pck!")
                
                found = True
                break
        except:
            pass
            
    if found:
        break

if not found:
    print("Key not found in .rdata or .data.")
