import pefile
from Cryptodome.Cipher import AES
import struct

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

# Get .rdata and .data raw data
sections_data = []
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name in (".rdata", ".data"):
        print(f"Adding section {name} (size: {sec.SizeOfRawData} bytes)")
        sections_data.append((name, sec.get_data()))

print("Starting version-based sliding-window scan...")
found = False

for name, sdata in sections_data:
    print(f"Scanning section {name}...")
    n_bytes = len(sdata)
    
    tested = 0
    for i in range(0, n_bytes - 32):
        candidate = sdata[i:i+32]
        tested += 1
        
        try:
            cipher = AES.new(candidate, AES.MODE_ECB)
            keystream = cipher.encrypt(c1)
            
            # Check if decrypted version (bytes 44..47, i.e. index 12..16 of c2) is 2 or 1
            # For version 2: keystream[12]^c2[12]==2, keystream[13]^c2[13]==0, keystream[14]^c2[14]==0, keystream[15]^c2[15]==0
            # For version 1: keystream[12]^c2[12]==1, keystream[13]^c2[13]==0, ...
            if (keystream[13] ^ c2_13) == 0 and (keystream[14] ^ c2_14) == 0 and (keystream[15] ^ c2_15) == 0:
                ver = keystream[12] ^ c2_12
                if ver in (1, 2):
                    # Fully verify using CFB
                    full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                    dec = full_cipher.decrypt(pck_data[16:])
                    pck_len = struct.unpack("<Q", dec[:8])[0]
                    
                    dec_magic = dec[40:44]
                    print(f"\nFOUND CANDIDATE KEY! Section: {name}, Offset: {hex(i)}")
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
        except Exception as e:
            pass
            
    if found:
        break

if not found:
    print("Key not found in .rdata or .data using version check.")
