import re

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

# Match ASCII strings of length >= 4
ascii_strings = re.findall(b"[a-zA-Z0-9_/.: -]{4,}", data)

with open("strings_dec.txt", "w") as out:
    for s in ascii_strings:
        try:
            out.write(s.decode() + "\n")
        except:
            pass

print(f"Extracted {len(ascii_strings)} strings from decrypted memory to strings_dec.txt!")
