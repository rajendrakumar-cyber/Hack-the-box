import pefile
from Cryptodome.Cipher import AES
import struct
import re

# Load PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

c1 = pck_data[32:48]
c2 = pck_data[48:64]

c2_8 = c2[8]
c2_9 = c2[9]
c2_10 = c2[10]
c2_11 = c2[11]

# Get .rdata and .data raw data
sections_data = []
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name in (".rdata", ".data", ".text"):
        sections_data.append((name, sec.get_data()))

print("Scanning for 64-character hex strings in sections...")
hex_pattern = re.compile(b"[0-9a-fA-F]{64}")

found = False
for name, sdata in sections_data:
    # Find all occurrences of 64 hex characters
    for match in hex_pattern.finditer(sdata):
        hex_str = match.group(0)
        try:
            # Convert hex string to 32 raw bytes
            candidate = bytes.fromhex(hex_str.decode())
            cipher = AES.new(candidate, AES.MODE_ECB)
            keystream = cipher.encrypt(c1)
            
            # Check magic GDPC
            if (keystream[8] ^ c2_8) == ord("G") and (keystream[9] ^ c2_9) == ord("D"):
                print(f"\nFOUND KEY AS HEX STRING! Section: {name}, Offset: {hex(match.start())}")
                print(f"Hex string: {hex_str.decode()}")
                
                full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                dec = full_cipher.decrypt(pck_data[16:])
                pck_len = struct.unpack("<Q", dec[:8])[0]
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
    print("No valid key found as hex string.")
