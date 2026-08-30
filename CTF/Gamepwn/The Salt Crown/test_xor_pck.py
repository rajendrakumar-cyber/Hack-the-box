with open("game.pck", "rb") as f:
    data = f.read()

# Expected plaintext headers
# Standard Godot PCK starts with:
# GDPC (4 bytes) + format (4 bytes, usually 1 or 2)
headers_to_test = [
    b"GDPC\x02\x00\x00\x00",
    b"GDPC\x01\x00\x00\x00",
    b"SCX1\x02\x00\x00\x00",
    b"SCX1\x01\x00\x00\x00",
]

found = False

for p_header in headers_to_test:
    # Derive XOR key assuming repeating key of length equal to len(p_header) (8 bytes)
    # or smaller factors (e.g. 4 bytes)
    for key_len in (4, 8):
        key = bytearray(key_len)
        for i in range(key_len):
            key[i] = data[i] ^ p_header[i]
            
        # Decrypt a portion of the file (say first 10KB) using this repeating XOR key
        dec = bytearray(min(len(data), 10000))
        for i in range(len(dec)):
            dec[i] = data[i] ^ key[i % key_len]
            
        # Check if "res://" is in the decrypted portion
        if b"res://" in dec:
            print(f"FOUND Repeating XOR key of length {key_len}!")
            print(f"Key (hex): {key.hex()}")
            print(f"Key (ASCII): {repr(key.decode(errors='ignore'))}")
            
            # Decrypt the entire file and save
            dec_full = bytearray(len(data))
            for i in range(len(data)):
                dec_full[i] = data[i] ^ key[i % key_len]
                
            with open("decrypted_game.pck", "wb") as out_f:
                out_f.write(dec_full)
            print("Saved decrypted pack to decrypted_game.pck!")
            found = True
            break
    if found:
        break

if not found:
    print("Repeating XOR key not found using standard headers.")
