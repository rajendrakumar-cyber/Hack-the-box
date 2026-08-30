import sys
from pwn import *
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

P = 0xCD4A96D3B7FA7251A1BB765933FB676FCAE8C9026682E34F779122DFD66915BB

def solve():
    # Connect to the server
    io = remote('154.57.164.72', 30794)
    
    # Receive intro and encrypted flag
    io.recvuntil(b"Here is something for you:\n")
    enc_flag_hex = io.recvline().strip().decode()
    log.info(f"Encrypted flag: {enc_flag_hex}")
    enc_flag = bytes.fromhex(enc_flag_hex)
    
    # Send G = P - 1
    G = P - 1
    io.sendlineafter(b"Before we start, give me the hashing generator: ", str(G).encode())
    
    # Recover key bits
    key_bits = [0] * 256
    for i in range(256):
        io.sendlineafter(b"> ", b"1")
        io.sendlineafter(b"Enter offset: ", str(i).encode())
        io.recvuntil(b"Oracle result: ")
        res = int(io.recvline().strip().decode())
        
        # If the result is 1 or P - 1, then the bit is 1
        if res == 1 or res == G:
            key_bits[i] = 1
        else:
            key_bits[i] = 0
            
    # Convert bits to bytes
    key_bin_str = "".join(map(str, key_bits))
    key_int = int(key_bin_str, 2)
    key_bytes = key_int.to_bytes(32, 'big')
    log.info(f"Recovered Key: {key_bytes.hex()}")
    
    # Decrypt flag
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    dec = cipher.decrypt(enc_flag)
    flag = unpad(dec, 16)
    print("FLAG:", flag.decode())
    
    io.close()

if __name__ == "__main__":
    solve()
