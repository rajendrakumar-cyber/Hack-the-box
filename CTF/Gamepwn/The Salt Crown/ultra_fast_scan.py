import pefile
from Cryptodome.Cipher import AES
import struct
import sys

# Load PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

# Ciphertext blocks
# IV: pck_data[0:16]
# C_0: pck_data[16:32]
# C_1: pck_data[32:48]
# C_2: pck_data[48:64]
c1 = pck_data[32:48]
c2 = pck_data[48:64]

# Get .rdata and .data raw data
sections_data = []
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name in (".rdata", ".data"):
        print(f"Adding section {name} (size: {sec.SizeOfRawData} bytes)")
        sections_data.append((name, sec.get_data()))

print("Starting ultra-fast sliding-window scan...")
found = False

for name, sdata in sections_data:
    print(f"Scanning section {name}...")
    
    # Split by null bytes to find non-zero chunks
    chunks = sdata.split(b"\x00")
    
    candidate_count = 0
    tested_count = 0
    
    for chunk in chunks:
        if len(chunk) >= 32:
            for j in range(len(chunk) - 31):
                candidate = chunk[j:j+32]
                candidate_count += 1
                
                try:
                    # Single block ECB encryption (which is just the raw AES block cipher)
                    cipher = AES.new(candidate, AES.MODE_ECB)
                    keystream = cipher.encrypt(c1)
                    tested_count += 1
                    
                    # Check if (keystream ^ c2)[8:12] == b"GDPC"
                    # XOR bytes 8 to 12
                    match = True
                    for k in range(4):
                        if (keystream[8+k] ^ c2[8+k]) != ord("GDPC"[k]):
                            match = False
                            break
                            
                    if match:
                        print(f"\nFOUND KEY! Section: {name}, Offset: {hex(sdata.find(candidate))}")
                        print(f"Key (hex): {candidate.hex()}")
                        
                        # Verify using full CFB mode
                        full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                        dec = full_cipher.decrypt(pck_data[16:])
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
    print("Key not found in zero-null chunks. Trying with 1-null chunks...")
    # Repeat scan allowing up to 1 null
    for name, sdata in sections_data:
        print(f"Scanning section {name} (allowing 1 null)...")
        chunks = sdata.split(b"\x00\x00")
        for chunk in chunks:
            if len(chunk) >= 32:
                for j in range(len(chunk) - 31):
                    candidate = chunk[j:j+32]
                    if candidate.count(0) > 1:
                        continue
                    try:
                        cipher = AES.new(candidate, AES.MODE_ECB)
                        keystream = cipher.encrypt(c1)
                        match = True
                        for k in range(4):
                            if (keystream[8+k] ^ c2[8+k]) != ord("GDPC"[k]):
                                match = False
                                break
                        if match:
                            print(f"\nFOUND KEY! Section: {name}")
                            print(f"Key (hex): {candidate.hex()}")
                            
                            full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                            dec = full_cipher.decrypt(pck_data[16:])
                            pck_len = struct.unpack("<Q", dec[:8])[0]
                            
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
