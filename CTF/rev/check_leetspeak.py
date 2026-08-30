s2 = [3, 7, 1, 5, 2, 6, 4, 0, 3, 7, 1, 5, 2, 6, 4, 0]
s3 = [3, 2, 3, 2, 5, 7, 2, 3, 5, 7, 2, 3, 5, 7, 2, 3]
s4 = [17, 122, 53, 144, 126, 136, 176, 89, 121, 127, 86, 106, 58, 16, 233, 5]

def rol8(x, k):
    return ((x << (k%8)) | (x >> (8-(k%8)))) & 255
def ror8(x, k):
    return ((x >> (k%8)) | (x << (8-(k%8)))) & 255

ops = {
    'rol': rol8, 'ror': ror8,
    'add': lambda x, k: (x + k) & 255,
    'sub': lambda x, k: (x - k) & 255,
    'xor': lambda x, k: x ^ k
}

# Generate common leetspeak candidates
candidates = []

# Variations of "keep your steel"
candidates.append(" k33p_y0ur_st33l")
candidates.append("k33p_y0ur_st33l ")
candidates.append("k33p_y0ur_st33l!")
candidates.append("k33p_y0ur_st33ls")
candidates.append("keep your steel ")
candidates.append(" keep your steel")

# Variations of "first mark"
candidates.append("the_f1rst_m4rk_")
candidates.append("_the_f1rst_m4rk")
candidates.append("f1rst_m4rk_v0w5")
candidates.append("f1rst_m4rk_st0n3")
candidates.append("v3yl3n_m4rr_v0w5")
candidates.append("f1rst_m4rk_steel")
candidates.append("f1rst_m4rk_st33l")

# Variations of "stone witnesses"
candidates.append("st0n3_w1tn3ss3s_")
candidates.append("st0n3_w1tn3ss3s!")
candidates.append("st0n3_w1tn3ss_v0")
candidates.append("th3_st0n3_v0w5_!")

# Variations of "read the four marks"
candidates.append("r34d_th3_4_m4rks")
candidates.append("r34d_th3_4_run3s")

# Let's also search for substrings or translations of "true"
candidates.append("true_true_true__")
candidates.append("vrai_vrai_vrai__")
candidates.append("verum_verum_veru")

for cand in candidates:
    if len(cand) != 16:
        continue
    cand_bytes = [ord(c) for c in cand]
    
    for name1, op1 in ops.items():
        for name2, op2 in ops.items():
            # Test Logic 1 (carry = val_old_a0 & state)
            state = 0xa5
            carry = 0
            matched = True
            for i in range(16):
                x = cand_bytes[i]
                val_old_a0 = op2(op1(x, s2[i]), s3[i])
                out = val_old_a0 ^ state ^ carry
                if out != s4[i]:
                    matched = False
                    break
                carry = val_old_a0 & state
                state = out
            if matched:
                print(f"Logic 1 MATCH! Candidate: {repr(cand)}, Rune 1: {name1}, Rune 2: {name2}")
                
            # Test Logic 2 (carry = x & state)
            state = 0xa5
            carry = 0
            matched = True
            for i in range(16):
                x = cand_bytes[i]
                val_old_a0 = op2(op1(x, s2[i]), s3[i])
                out = val_old_a0 ^ state ^ carry
                if out != s4[i]:
                    matched = False
                    break
                carry = x & state
                state = out
            if matched:
                print(f"Logic 2 MATCH! Candidate: {repr(cand)}, Rune 1: {name1}, Rune 2: {name2}")
