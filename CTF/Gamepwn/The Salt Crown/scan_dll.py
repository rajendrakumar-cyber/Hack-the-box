from Cryptodome.Cipher import AES
import struct

with open("game.pck", "rb") as f:
    pck_data = f.read(128)

c1 = pck_data[32:48]
c2 = pck_data[48:64]

with open("decrypted_memory.bin", "rb") as f:
    sdata = f.read()

n_bytes = len(sdata)
print(f"Scanning GDExtension DLL (size: {n_bytes} bytes)...")

g_ord = ord("G")
d_ord = ord("D")
p_ord = ord("P")
c_ord = ord("C")

c2_8 = c2[8]
c2_9 = c2[9]
c2_10 = c2[10]
c2_11 = c2[11]

found = False
for i in range(0, n_bytes - 32):
    candidate = sdata[i:i+32]
    try:
        cipher = AES.new(candidate, AES.MODE_ECB)
        keystream = cipher.encrypt(c1)
        
        if (keystream[8] ^ c2_8) == g_ord:
            if (keystream[9] ^ c2_9) == d_ord:
                if (keystream[10] ^ c2_10) == p_ord:
                    if (keystream[11] ^ c2_11) == c_ord:
                        full_cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                        dec = full_cipher.decrypt(pck_data[16:])
                        pck_len = struct.unpack("<Q", dec[:8])[0]
                        
                        print(f"\nFOUND KEY IN DLL! Offset: {hex(i)}")
                        print(f"Key (hex): {candidate.hex()}")
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

if not found:
    print("Key not found in GDExtension DLL.")
