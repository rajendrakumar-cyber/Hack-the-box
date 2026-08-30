import pefile
from Cryptodome.Cipher import AES
import struct

# Load PE file and game.pck
pe = pefile.PE("The Salt Crown.exe")

with open("game.pck", "rb") as f:
    pck_data = f.read(256)

# Get data sections
sections_data = []
for sec in pe.sections:
    name = sec.Name.decode().strip("\x00")
    if name in (".rdata", ".data"):
        print(f"Adding section {name} (size: {sec.SizeOfRawData} bytes)")
        sections_data.append((name, sec.get_data()))

print("Starting all-mode scanning...")
found = False

# We will split by nulls first for speed
for name, sdata in sections_data:
    print(f"Scanning section {name}...")
    chunks = sdata.split(b"\x00")
    
    tested = 0
    for chunk in chunks:
        if len(chunk) >= 32:
            for j in range(len(chunk) - 31):
                candidate = chunk[j:j+32]
                tested += 1
                
                # We will test:
                # 1. CFB mode, IV at start (offset 16)
                # 2. CFB mode, IV is constant/zeros (offset 0)
                # 3. CBC mode, IV at start
                # 4. CBC mode, IV is constant/zeros
                # 5. ECB mode
                
                # We can test these quickly by decrypting the first 64/80 bytes
                
                # Test 1 & 3: IV at start (ciphertext from 16)
                try:
                    # CFB
                    cipher = AES.new(candidate, AES.MODE_CFB, iv=pck_data[:16], segment_size=128)
                    dec = cipher.decrypt(pck_data[16:96])
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY (CFB, IV-start)! Key: {candidate.hex()}")
                        found = True
                        break
                except:
                    pass
                
                # Test 2 & 4: IV is zeros (ciphertext from 0)
                try:
                    # CFB
                    zero_iv = b"\x00" * 16
                    cipher = AES.new(candidate, AES.MODE_CFB, iv=zero_iv, segment_size=128)
                    dec = cipher.decrypt(pck_data[:96])
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY (CFB, Zero-IV)! Key: {candidate.hex()}")
                        found = True
                        break
                except:
                    pass
                
                # Test 3: CBC, IV at start
                try:
                    cipher = AES.new(candidate, AES.MODE_CBC, iv=pck_data[:16])
                    dec = cipher.decrypt(pck_data[16:96])
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY (CBC, IV-start)! Key: {candidate.hex()}")
                        found = True
                        break
                except:
                    pass
                
                # Test 4: CBC, Zero-IV
                try:
                    zero_iv = b"\x00" * 16
                    cipher = AES.new(candidate, AES.MODE_CBC, iv=zero_iv)
                    dec = cipher.decrypt(pck_data[:96])
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY (CBC, Zero-IV)! Key: {candidate.hex()}")
                        found = True
                        break
                except:
                    pass
                
                # Test 5: ECB
                try:
                    cipher = AES.new(candidate, AES.MODE_ECB)
                    dec = cipher.decrypt(pck_data[:96])
                    if dec[40:44] == b"GDPC":
                        print(f"\nFOUND KEY (ECB)! Key: {candidate.hex()}")
                        found = True
                        break
                except:
                    pass
            if found:
                break
    if found:
        break

if not found:
    print("Key not found in zero-null chunks of data sections.")
