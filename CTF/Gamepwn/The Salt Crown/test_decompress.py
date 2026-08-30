import zlib
import gzip

# Try to import zstd and lz4 if available
try:
    import zstd
except ImportError:
    zstd = None

try:
    import lz4.block as lz4
except ImportError:
    lz4 = None

with open("game.pck", "rb") as f:
    data = f.read()

print(f"File size: {len(data)} bytes")
print(f"Header: {data[:16].hex()}")

# Try different header sizes (4, 8, 12, 16)
for header_size in (4, 8, 12, 16):
    payload = data[header_size:]
    
    # 1. Try Zlib / Deflate
    try:
        dec = zlib.decompress(payload)
        print(f"SUCCESS (Zlib) at header size {header_size}! Decressed size: {len(dec)}")
        if dec[:4] == b"GDPC":
            print("Found decrypted PCK magic GDPC!")
            with open("decompressed_game.pck", "wb") as out_f:
                out_f.write(dec)
            break
    except:
        pass

    # Try raw deflate (wbits=-15)
    try:
        dec = zlib.decompress(payload, -15)
        print(f"SUCCESS (Raw Deflate) at header size {header_size}! Decressed size: {len(dec)}")
        if dec[:4] == b"GDPC":
            print("Found decrypted PCK magic GDPC!")
            with open("decompressed_game.pck", "wb") as out_f:
                out_f.write(dec)
            break
    except:
        pass

    # 2. Try Gzip
    try:
        dec = gzip.decompress(payload)
        print(f"SUCCESS (Gzip) at header size {header_size}! Decressed size: {len(dec)}")
        if dec[:4] == b"GDPC":
            print("Found decrypted PCK magic GDPC!")
            with open("decompressed_game.pck", "wb") as out_f:
                out_f.write(dec)
            break
    except:
        pass

    # 3. Try Zstd
    if zstd:
        try:
            dec = zstd.decompress(payload)
            print(f"SUCCESS (Zstd) at header size {header_size}! Decressed size: {len(dec)}")
            if dec[:4] == b"GDPC":
                print("Found decrypted PCK magic GDPC!")
                with open("decompressed_game.pck", "wb") as out_f:
                    out_f.write(dec)
                break
        except:
            pass

    # 4. Try LZ4
    if lz4:
        try:
            # We might need to guess the uncompressed size or use decompress
            dec = lz4.decompress(payload)
            print(f"SUCCESS (LZ4) at header size {header_size}! Decressed size: {len(dec)}")
            if dec[:4] == b"GDPC":
                print("Found decrypted PCK magic GDPC!")
                with open("decompressed_game.pck", "wb") as out_f:
                    out_f.write(dec)
                break
        except:
            pass
