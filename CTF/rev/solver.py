def rol8(x, k):
    k = k % 8
    return ((x << k) | (x >> (8 - k))) & 255

def ror8(x, k):
    k = k % 8
    return ((x >> k) | (x << (8 - k))) & 255

s2 = [3, 7, 1, 5, 2, 6, 4, 0, 3, 7, 1, 5, 2, 6, 4, 0]
s3 = [3, 2, 3, 2, 5, 7, 2, 3, 5, 7, 2, 3, 5, 7, 2, 3]
s4 = [17, 122, 53, 144, 126, 136, 176, 89, 121, 127, 86, 106, 58, 16, 233, 5]

# 1. Reverse Rune 3 (Stateful carry-save XOR)
state = 0xa5
carry = 0
old_a0 = []
for out in s4:
    x = out ^ state ^ carry
    old_a0.append(x)
    carry = x & state
    state = out

# 2. Reverse Rune 2 (ror) and Rune 1 (rol)
# op2(op1(x, k1), k2) == y
# ror(rol(x, k1), k2) == y  =>  rol(x, k1) == rol(y, k2)  =>  x == ror(rol(y, k2), k1)
flag_bytes = []
for i in range(16):
    y = old_a0[i]
    k1 = s2[i] & 7
    k2 = s3[i]
    val1 = rol8(y, k2)
    x = ror8(val1, k1)
    flag_bytes.append(x)

flag = "HTB{" + "".join(f"{b:02x}" for b in flag_bytes) + "}"
print("Flag:", flag)
