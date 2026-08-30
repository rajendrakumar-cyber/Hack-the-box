import re
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def find_all_solutions(A, B):
    n = len(A)
    pivot_cols = []
    pivot_rows = []
    row = 0
    for col in range(n):
        pivot = -1
        for r in range(row, n):
            if A[r][col] == 1:
                pivot = r
                break
        if pivot != -1:
            A[row], A[pivot] = A[pivot], A[row]
            B[row], B[pivot] = B[pivot], B[row]
            for r in range(row + 1, n):
                if A[r][col] == 1:
                    for c in range(col, n):
                        A[r][c] ^= A[row][c]
                    B[r] ^= B[row]
            pivot_cols.append(col)
            pivot_rows.append(row)
            row += 1
            
    # Check consistency
    for r in range(row, n):
        if B[r] != 0:
            return []
            
    free_cols = [c for c in range(n) if c not in pivot_cols]
    num_free = len(free_cols)
    print(f"Pivots: {len(pivot_cols)}, Free variables: {num_free}")
    
    solutions = []
    for mask in range(1 << num_free):
        X = [0] * n
        for idx, col in enumerate(free_cols):
            X[col] = (mask >> idx) & 1
            
        for r, col in reversed(list(zip(pivot_rows, pivot_cols))):
            val = B[r]
            for c in range(col + 1, n):
                val ^= A[r][c] * X[c]
            X[col] = val
        solutions.append(X)
        
    return solutions

def main():
    # Read output.txt
    with open('crypto_ashen_field/output.txt', 'r') as f:
        lines = f.readlines()
        
    polys_str = lines[0].strip()[1:-1]
    polys = polys_str.split(', ')
    encrypted_key = eval(lines[1].strip())
    enc_flag = bytes.fromhex(lines[2].strip())
    
    N = 137
    A = [[0] * N for _ in range(N)]
    B = [0] * N
    
    for i in range(N):
        poly = polys[i]
        terms = poly.split(' + ')
        counts = [0] * N
        const = 0
        for term in terms:
            term = term.strip()
            if term == '1':
                const ^= 1
            else:
                match = re.match(r'x(\d+)', term)
                if match:
                    idx = int(match.group(1)) - 1
                    counts[idx] ^= 1
                    
        for j in range(N):
            A[i][j] = counts[j]
        B[i] = encrypted_key[i] ^ const
        
    # Solve linear system
    sols = find_all_solutions(A, B)
    print(f"Found {len(sols)} possible keys. Trying decryption...")
    
    for idx, X in enumerate(sols):
        KEY = sum(X[i] * (2**i) for i in range(N))
        AES_KEY = hashlib.sha256(str(KEY).encode()).digest()
        cipher = AES.new(AES_KEY, AES.MODE_ECB)
        dec = cipher.decrypt(enc_flag)
        try:
            flag = unpad(dec, 16)
            print(f"SUCCESS (sol {idx})!")
            print("FLAG:", flag.decode())
            break
        except Exception:
            pass

if __name__ == '__main__':
    main()
