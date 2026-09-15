import struct
import json
from datetime import datetime
from collections import defaultdict
from Crypto.Cipher import AES, ARC4
from Crypto.Util import Counter

KEY = bytes.fromhex("f05d9b66d1877dffb5d46f9ea92669ef")

TARGET_PATTERNS = [
    b"CTF{", b"ctf{", b"IATCQ", b"iatcq", b"AQL", b"aql",
    b"recipe", b"Recipe", b"Aqualis", b"Rivera",
    b"%PDF", b"PK\x03\x04", b"\x1f\x8b", b"BZh", b"7z\xbc\xaf\x27\x1c"
]

def check_content(data, desc):
    if not data:
        return
    for pat in TARGET_PATTERNS:
        if pat in data:
            print(f"[!] MATCH FOUND [{pat.decode('latin1', 'replace')}]: {desc}")
            print(f"    Snippet: {data[:200]}")
            return True
    # Also check if mostly printable ASCII (printable ratio > 0.85 and len > 20)
    if len(data) >= 30:
        printable = sum(1 for b in data[:100] if 32 <= b <= 126 or b in (9, 10, 13))
        if printable / min(len(data), 100) > 0.85:
            print(f"[?] HIGH ASCII RATIO ({printable}%): {desc}")
            print(f"    Snippet: {data[:100]}")
            return True
    return False

def pack_bits(bits, msb=True):
    n = len(bits) - (len(bits) % 8)
    out = bytearray()
    for i in range(0, n, 8):
        chunk = bits[i:i+8]
        if not msb:
            chunk = chunk[::-1]
        val = 0
        for b in chunk:
            val = (val << 1) | b
        out.append(val)
    return bytes(out)

def test_all_ciphers(raw_bytes, desc):
    # 1. Plain
    check_content(raw_bytes, f"{desc} (PLAIN)")
    
    # 2. XOR with KEY
    for k_off in range(16):
        xored = bytes(raw_bytes[i] ^ KEY[(i + k_off) % 16] for i in range(len(raw_bytes)))
        check_content(xored, f"{desc} (XOR k_off={k_off})")
        
    # 3. ARC4
    try:
        dec = ARC4.new(KEY).decrypt(raw_bytes)
        check_content(dec, f"{desc} (ARC4)")
    except Exception:
        pass
        
    # 4. AES modes
    if len(raw_bytes) >= 16:
        # AES-ECB
        b_aes = raw_bytes[:len(raw_bytes) - (len(raw_bytes) % 16)]
        try:
            dec = AES.new(KEY, AES.MODE_ECB).decrypt(b_aes)
            check_content(dec, f"{desc} (AES-ECB)")
        except Exception:
            pass
            
        # AES-CBC IV=0
        try:
            dec = AES.new(KEY, AES.MODE_CBC, iv=b'\x00'*16).decrypt(b_aes)
            check_content(dec, f"{desc} (AES-CBC iv=0)")
        except Exception:
            pass
            
        # AES-CBC IV=first block
        if len(raw_bytes) >= 32:
            try:
                dec = AES.new(KEY, AES.MODE_CBC, iv=raw_bytes[:16]).decrypt(b_aes[16:])
                check_content(dec, f"{desc} (AES-CBC iv=block0)")
            except Exception:
                pass
                
        # AES-CTR
        try:
            dec = AES.new(KEY, AES.MODE_CTR, counter=Counter.new(128)).decrypt(raw_bytes)
            check_content(dec, f"{desc} (AES-CTR cnt=0)")
        except Exception:
            pass
        try:
            dec = AES.new(KEY, AES.MODE_CTR, nonce=b'\x00'*8).decrypt(raw_bytes)
            check_content(dec, f"{desc} (AES-CTR nonce=0)")
        except Exception:
            pass
        if len(raw_bytes) > 16:
            try:
                dec = AES.new(KEY, AES.MODE_CTR, nonce=raw_bytes[:8]).decrypt(raw_bytes[8:])
                check_content(dec, f"{desc} (AES-CTR nonce=b[:8])")
            except Exception:
                pass

def test_bitstream(bits, name):
    for inv in [False, True]:
        b_list = [1 - b for b in bits] if inv else bits
        for msb in [True, False]:
            for shift in range(8):
                b_bytes = pack_bits(b_list[shift:], msb=msb)
                inv_str = "INV" if inv else "NORM"
                msb_str = "MSB" if msb else "LSB"
                test_all_ciphers(b_bytes, f"{name} {inv_str} {msb_str} s={shift}")

print("Test decoders defined.")
