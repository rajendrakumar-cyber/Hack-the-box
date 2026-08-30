import string

with open("decrypted_memory.bin", "rb") as f:
    data = f.read()

strings = []
curr = []
for b in data:
    if chr(b) in string.printable and b >= 32 and b < 127:
        curr.append(chr(b))
    else:
        if len(curr) >= 4:
            strings.append("".join(curr))
        curr = []
if len(curr) >= 4:
    strings.append("".join(curr))

# Deduplicate but preserve order
seen = set()
unique_strings = []
for s in strings:
    if s not in seen:
        seen.add(s)
        unique_strings.append(s)

with open("strings_dll.txt", "w") as f:
    for s in unique_strings:
        f.write(s + "\n")

print(f"Extracted {len(unique_strings)} unique strings to strings_dll.txt!")
