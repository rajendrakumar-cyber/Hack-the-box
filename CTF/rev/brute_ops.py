import string

s2 = [3, 7, 1, 5, 2, 6, 4, 0, 3, 7, 1, 5, 2, 6, 4, 0]
s3 = [3, 2, 3, 2, 5, 7, 2, 3, 5, 7, 2, 3, 5, 7, 2, 3]
s4 = [17, 122, 53, 144, 126, 136, 176, 89, 121, 127, 86, 106, 58, 16, 233, 5]

# Set of allowed chars for the syllable
allowed = set(ord(c) for c in string.printable if c not in '\r\n\t\x0b\x0c')

def rol8(x, k):
    k = k % 8
    return ((x << k) | (x >> (8 - k))) & 255

def ror8(x, k):
    k = k % 8
    return ((x >> k) | (x << (8 - k))) & 255

ops = {
    'rol': rol8,
    'ror': ror8,
    'add': lambda x, k: (x + k) & 255,
    'sub': lambda x, k: (x - k) & 255,
    'xor': lambda x, k: x ^ k,
    'sll': lambda x, k: (x << k) & 255,
    'srl': lambda x, k: x >> k
}

# Test standard carry logic: carry = val_old_a0 & state
# state = 0xa5, carry = 0
state = 0xa5
carry = 0
old_a0_standard = []
for i in range(16):
    out = s4[i]
    val_old_a0 = out ^ state ^ carry
    old_a0_standard.append(val_old_a0)
    carry = val_old_a0 & state
    state = out

print("--- Standard Carry Logic ---")
for name1, op1 in ops.items():
    for name2, op2 in ops.items():
        candidate = []
        possible = True
        for i in range(16):
            y = old_a0_standard[i]
            k1 = s2[i]
            k2 = s3[i]
            # Solve for x: op2(op1(x, k1), k2) == y
            found_x = None
            for x in range(256):
                if op2(op1(x, k1), k2) == y:
                    found_x = x
                    break
            if found_x is None or found_x not in allowed:
                possible = False
                break
            candidate.append(chr(found_x))
            
        if possible:
            print(f"Match! Rune 1: {name1}, Rune 2: {name2} -> {''.join(candidate)}")

# Test alternative carry logic: carry = x & state
print("--- Alternative Carry Logic ---")
for name1, op1 in ops.items():
    for name2, op2 in ops.items():
        candidate = []
        possible = True
        state = 0xa5
        carry = 0
        for i in range(16):
            target = s4[i]
            k1 = s2[i]
            k2 = s3[i]
            found_x = None
            for x in range(256):
                val1 = op1(x, k1)
                val_old_a0 = op2(val1, k2)
                out = val_old_a0 ^ state ^ carry
                if out == target:
                    found_x = x
                    break
            if found_x is None or found_x not in allowed:
                possible = False
                break
            candidate.append(chr(found_x))
            carry = found_x & state
            state = target
            
        if possible:
            print(f"Match! Rune 1: {name1}, Rune 2: {name2} -> {''.join(candidate)}")
