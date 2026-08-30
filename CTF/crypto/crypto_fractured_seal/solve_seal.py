import base64
import sys
import math
import decimal
from fpylll import IntegerMatrix, LLL
from Crypto.Util.number import long_to_bytes, bytes_to_long

decimal.getcontext().prec = 150
D = decimal.Decimal

def eval_poly(coeffs, x):
    val = D(0)
    for c in reversed(coeffs):
        val = val * x + D(c)
    return val

def eval_deriv(coeffs, x):
    deriv_coeffs = [i * coeffs[i] for i in range(1, len(coeffs))]
    val = D(0)
    for c in reversed(deriv_coeffs):
        val = val * x + D(c)
    return val

def newton_roots(coeffs, X_max):
    roots = set()
    # 11 starting points is more than enough for a degree 13 polynomial
    for i in range(-5, 6):
        x = D(i) * D(X_max) / D(5)
        for _ in range(50):
            fx = eval_poly(coeffs, x)
            dfx = eval_deriv(coeffs, x)
            if dfx == 0:
                break
            dx = fx / dfx
            x -= dx
            if abs(dx) < 1:
                break
        r_int = int(round(x))
        # Exact integer check
        val = 0
        p_x = 1
        for c in coeffs:
            val += c * p_x
            p_x *= r_int
        if val == 0:
            roots.add(r_int)
    return list(roots)

def coppersmith_msb(N, p0, X, m=7, t=6):
    d = m + t
    M = IntegerMatrix(d, d)
    for i in range(d):
        if i < m:
            for k in range(i + 1):
                M[i, k] = int((N**(m-i)) * math.comb(i, k) * (p0**(i-k)) * (X**k))
        else:
            j = i - m
            for k_bin in range(m + 1):
                k = j + k_bin
                M[i, k] = int(math.comb(m, k_bin) * (p0**(m-k_bin)) * (X**k))
                
    # Run LLL
    LLL.reduction(M)
    
    # We ONLY check the first row (the shortest vector), which is guaranteed to contain the root
    row = [int(M[0, k]) for k in range(d)]
    coeffs = []
    for k in range(d):
        c_k = row[k] // (X**k)
        coeffs.append(c_k)
        
    roots = newton_roots(coeffs, X)
    for r_int in roots:
        p = p0 + r_int
        if p > 1 and N % p == 0:
            return p
            
    return None

def main():
    prefix = 'MIIEowIBAAKCAQEAjK59ahXlX7a+oF+jt5icukpGeNXXgQO4D3jPeLaGAupJm6a69PnWCf0W3QDhmCPxLYWSr1C4DvxP23UlvP8Lcfu+w/oIS0jDHkfnv+m1Qku/ii9wehy/iRNuUeaH88K4AA0XFvJoak5I0Igi5ksP/CsyGMRJbUe898eLZjYOYAoA2+fiLjjfYDBHliyXrva55W9O2ie2SNZ2Q859kAb0IQj/DK3LuAHqtuE7HVm2KDydU0jjiMFz5uhwcU5njXnHdZRfrCTaUWBLLxmE8PCbIuy8hJqhL+iD1OcwTS8Yo8xoTtoc7HFFfXYNoKjnqgp+LOmLwQGQeO2Yo1Hb8SCV'
    data = base64.b64decode(prefix)
    n_bytes_known = data[12:]
    
    prefix_full = 'MIIEowIBAAKCAQEAjK59ahXlX7a+oF+jt5icukpGeNXXgQO4D3jPeLaGAupJm6a69PnWCf0W3QDhmCPxLYWSr1C4DvxP23UlvP8Lcfu+w/oIS0jDHkfnv+m1Qku/ii9wehy/iRNuUeaH88K4AA0XFvJoak5I0Igi5ksP/CsyGMRJbUe898eLZjYOYAoA2+fiLjjfYDBHliyXrva55W9O2ie2SNZ2Q859kAb0IQj/DK3LuAHqtuE7HVm2KDydU0jjiMFz5uhwcU5njXnHdZRfrCTaUWBLLxmE8PCbIuy8hJqhL+iD1OcwTS8Yo8xoTtoc7HFFfXYNoKjnqgp+LOmLwQGQeO2Yo1Hb8SCVd'
    frag2 = '2msCgYEAwLGxcJ7/YCgq9GPDS16cHPNZEmYrbSX+atzUBBO2jLYg0QbXfitTIHfU+55DqIxFQOcu+CahrPQQROoZAAIPg0LdaGd+3R3/ri'
    padded_b64 = prefix_full + 'A' * 527 + frag2
    padded_b64 += '=' * ((4 - len(padded_b64)%4)%4)
    data2 = base64.b64decode(padded_b64)
    p_bytes_known = data2[669:669+72]
    
    P_known_val = bytes_to_long(p_bytes_known)
    N_known_val = bytes_to_long(n_bytes_known)
    
    enc_flag = open('crypto_fractured_seal/flag.enc', 'rb').read()
    c = bytes_to_long(enc_flag)
    
    N_base = N_known_val << 8
    X_max = 2**448
    p0 = P_known_val << 448
    
    print("Starting Coppersmith MSB factorization search...")
    for last_byte in range(1, 256, 2):
        N = N_base + last_byte
        p = coppersmith_msb(N, p0, X_max, m=7, t=6)
        if p is not None:
            q = N // p
            print(f"SUCCESS! Found factors for N candidate ending in {last_byte}:")
            print("p =", p)
            print("q =", q)
            print("N =", N)
            
            phi = (p - 1) * (q - 1)
            e = 0x10001
            d = pow(e, -1, phi)
            m = pow(c, d, N)
            flag = long_to_bytes(m)
            print("FLAG:", flag.decode())
            sys.exit(0)
            
    print("Search finished. No key found.")

if __name__ == '__main__':
    main()
