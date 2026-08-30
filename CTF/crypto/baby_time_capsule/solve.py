import socket
import json
from Crypto.Util.number import long_to_bytes

def solve_crt(remainders, moduli):
    # Chinese Remainder Theorem
    # x = remainders[i] mod moduli[i]
    total_modulus = 1
    for m in moduli:
        total_modulus *= m
    
    result = 0
    for r, m in zip(remainders, moduli):
        M = total_modulus // m
        y = pow(M, -1, m)
        result += r * M * y
    
    return result % total_modulus

def nth_root(n, k):
    # Find integer k-th root of n using binary search
    low = 0
    high = n
    while low <= high:
        mid = (low + high) // 2
        mid_k = mid ** k
        if mid_k == n:
            return mid
        elif mid_k < n:
            low = mid + 1
        else:
            high = mid - 1
    return high

def main():
    host = "154.57.164.67"
    port = 31247
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    
    ciphertexts = []
    moduli = []
    e = 5
    
    for i in range(e):
        # Receive prompt
        prompt = s.recv(1024)
        print(f"Prompt: {prompt}")
        
        # Send Y
        s.sendall(b"Y\n")
        
        # Receive response
        response = b""
        while b"\n" not in response:
            response += s.recv(1)
        
        print(f"Received: {response.decode().strip()}")
        data = json.loads(response.decode().strip())
        
        c = int(data["time_capsule"], 16)
        n = int(data["pubkey"][0], 16)
        
        ciphertexts.append(c)
        moduli.append(n)
        
    s.close()
    
    # CRT
    c_combined = solve_crt(ciphertexts, moduli)
    
    # Get 5th root
    m = nth_root(c_combined, e)
    
    # Decode to bytes
    flag = long_to_bytes(m)
    print(f"Recovered FLAG: {flag.decode()}")

if __name__ == "__main__":
    main()
