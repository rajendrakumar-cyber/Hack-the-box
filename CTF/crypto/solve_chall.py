# Solve script for chall.py

def decrypt(ct_hex):
    ct = bytes.fromhex(ct_hex)
    inv = pow(123, -1, 256)
    
    pt = []
    for c in ct:
        pt.append(((c - 18) * inv) % 256)
        
    return bytes(pt).decode('utf-8', errors='ignore')

def main():
    with open('./msg.enc', 'r') as f:
        ct_hex = f.read().strip()
        
    flag = decrypt(ct_hex)
    print(f"Decrypted flag: {flag}")

if __name__ == "__main__":
    main()
