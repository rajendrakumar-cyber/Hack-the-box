# Search for the byte sequence gcz\xf0 (67 63 7a f0)

def search_pattern(filename, pattern):
    print(f"Searching for pattern in {filename}...")
    with open(filename, "rb") as f:
        data = f.read()
    
    offsets = []
    idx = data.find(pattern)
    while idx != -1:
        offsets.append(idx)
        idx = data.find(pattern, idx + 1)
        
    for offset in offsets:
        print(f"  Found at offset {hex(offset)}")
    return len(offsets)

pat1 = b"gcz\xf0"
pat2 = b"\xf0zcg"

print("Pattern 1 (gcz\\xf0):")
c1 = search_pattern("decrypted_memory.bin", pat1)
c2 = search_pattern("The Salt Crown.exe", pat1)

print("\nPattern 2 (\\xf0zcg):")
c3 = search_pattern("decrypted_memory.bin", pat2)
c4 = search_pattern("The Salt Crown.exe", pat2)
