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

print("Starting optimized null-split sliding-window scan...")
found = False

for name, sdata in sections_data:
    print(f"Scanning section {name}...")
    
    # We split by null bytes to find continuous blocks of non-zero bytes of length >= 32.
    # An AES key generated randomly is extremely unlikely to have even one null byte, 
    # and virtually impossible to have more than 1. So splitting by b'\x00' is safe and extremely fast.
    chunks = sdata.split(b"\x00")
    
    candidate_count = 0
    tested_count = 0
    
    for chunk in chunks:
        if len(chunk) >= 32:
            # We also allow up to 1 null byte in case the key has a null.
            # But let's first test the 0-null chunks (which is what split(b'\x00') gives us).
            # If that fails, we can do a split by 2 consecutive nulls.
            for j in range(len(chunk) - 31):
                candidate = chunk[j:j+32]
                candidate_count += 1
                
                try:
                    cipher = AES.new(candidate, AES.MODE_CFB, iv=iv, segment_size=128)
                    dec = cipher.decrypt(ciphertext)
                    tested_count += 1
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY! Section: {name}")
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
                except Exception as e:
                    pass
            if found:
                break
                
    print(f"Tested {tested_count} candidates from {candidate_count} possibilities in {name}.")
    if found:
        break

if not found:
    print("Key not found in zero-null chunks. Let's try allowing 1 null byte...")
    # To allow up to 1 null byte, we can split by b'\x00\x00' (two consecutive null bytes).
    # Then each chunk has at most isolated single null bytes.
    for name, sdata in sections_data:
        print(f"Scanning section {name} (allowing 1 null)...")
        chunks = sdata.split(b"\x00\x00")
        for chunk in chunks:
            if len(chunk) >= 32:
                # Iterate and extract 32-byte slices
                for j in range(len(chunk) - 31):
                    candidate = chunk[j:j+32]
                    # Filter: must have at most 1 null byte
                    if candidate.count(0) > 1:
                        continue
                    try:
                        cipher = AES.new(candidate, AES.MODE_CFB, iv=iv, segment_size=128)
                        dec = cipher.decrypt(ciphertext)
                        if dec[40:44] == b"GDPC":
                            print(f"\nFOUND KEY! Section: {name}")
                            print(f"Key (hex): {candidate.hex()}")
                            pck_len = struct.unpack("<Q", dec[:8])[0]
                            print(f"Decrypted Pack Length: {pck_len}")
                            
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
        if found:
            break

if not found:
    print("Key not found.")
