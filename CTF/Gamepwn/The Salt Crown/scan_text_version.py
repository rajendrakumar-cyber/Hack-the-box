import pefile
from Cryptodome.Cipher import AES
import struct
import time

# Load PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

c1 = pck_data[32:48]
c2 = pck_data[48:64]

c2_12 = c2[12]
c2_13 = c2[13]
c2_14 = c2[14]
c2_15 = c2[15]

# Locate .text section
text_sec = None
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name == ".text":
        text_sec = sec
        break

if not text_sec:
    print("Could not find .text section")
    exit(1)

sdata = text_sec.get_data()
print("Starting version-based scan on .text (zero-null chunks)...")
t_start = time.time()

# Split by null bytes
chunks = sdata.split(b"\x00")
print(f"Split .text into {len(chunks)} chunks.")

candidate_count = 0
tested_count = 0
found = False

for chunk in chunks:
    if len(chunk) >= 32:
        for j in range(len(chunk) - 31):
            candidate = chunk[j:j+32]
            candidate_count += 1
            
            try:
                # CFB mode first block: keystream = AES(key, c1)
                cipher = AES.new(candidate, AES.MODE_ECB)
                keystream = cipher.encrypt(c1)
                tested_count += 1
                
                # Check version byte
                if (keystream[13] ^ c2_13) == 0 and (keystream[14] ^ c2_14) == 0 and (keystream[15] ^ c2_15) == 0:
                    ver = keystream[12] ^ c2_12
                    if ver in (1, 2):
                        # Verify using CFB
                        full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                        dec = full_cipher.decrypt(pck_data[16:])
                        pck_len = struct.unpack("<Q", dec[:8])[0]
                        dec_magic = dec[40:44]
                        
                        print(f"\nFOUND KEY IN .text! Offset: {hex(sdata.find(candidate))}")
                        print(f"Key (hex): {candidate.hex()}")
                        print(f"Decrypted Magic: {dec_magic} ({dec_magic.decode(errors='ignore')})")
                        print(f"Decrypted Version: {ver}")
                        print(f"Decrypted Pack Length: {pck_len}")
                        
                        # Decrypt and save
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

t_end = time.time()
print(f"Tested {tested_count} candidates from {candidate_count} possibilities.")
print(f"Scan finished in {t_end - t_start:.4f} seconds.")
if not found:
    print("Key not found in zero-null chunks of .text using version check.")
