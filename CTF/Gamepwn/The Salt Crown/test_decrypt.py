from Cryptodome.Cipher import AES
import struct

with open("game.pck", "rb") as f:
    data = f.read(256)

iv = data[:16]
ciphertext = data[16:]

keys = [
    "31f5b28ec39bdc74a0988c2c45f49542473c69d6c501e5a1709003c178220748",
    "bd3e420f63f59489e359e6a9dac8ac21e1e43930558ee04fa19bf123c01f9d77",
    "326a57358d364da252337c6de5df3853723fdd9b854307be5c1caab83e230b4a",
    "d1c88ba4679afffdecf691c26b02253258970b5941854c08a6746ddfe4c0f20c",
    "8def1d38cdf7106a6e4ce0ba75c25bc7780b72f08ab5695e54b632ca076d8620",
    "c354c9187963649e3e0670ee65fd8ffc8a325a3f264bebb74c90bf48c25cf9a1",
    "b37c6fb8e36506fc6dd81f60c473c385bd9caf0878bced4d87769a3e74dee12e",
    "df4fb19d03abb0ef99c91f44a38d2a5fe02e9469b55a13de65f7d8a74c3db6c2",
    "dcfe46ad0728f2a8d71588ca184ac2d10f7dd82a7e1dbffd4221eb78bd504be3",
    "d237852eeb9006b73e9302cca9f1e0f97c39caf201070a25ade7736d2b6b9892",
    "182eef2fad42f75467225f3d239730198d6cc6ebe56b9e665737c443524da4e8",
    "e14899e7a7717ab80d4f469fdd2e952b79012cf7b5511a767fc76268c212905a",
    "b071665716e3880109e991cbf033301e7fd075deba951223226874f8a2e2a63c",
    "429dd1b2cce386a71ec9ad0730d35068377bf033d773ee8d889a8f6f189cc77c",
    "a39f39acf2fde265208f8e8276851025837d1d7b476c6a6d707371cb7427384b"
]

print("Testing CFB mode...")
for key_hex in keys:
    key = bytes.fromhex(key_hex)
    try:
        # In Godot 4, FileAccessEncrypted uses CFB mode
        cipher = AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128)
        dec = cipher.decrypt(ciphertext)
        
        # In FileAccessEncrypted:
        # - Decrypted bytes 0-7: length (uint64)
        # - Decrypted bytes 8-39: hash (32 bytes)
        # - Decrypted bytes 40+: raw PCK starting with GDPC
        magic = dec[40:44]
        if magic == b"GDPC":
            print(f"FOUND KEY! Key (hex): {key_hex}")
            print(f"Decrypted length: {struct.unpack('<Q', dec[:8])[0]}")
            break
    except Exception as e:
        pass

print("\nTesting CBC mode just in case...")
for key_hex in keys:
    key = bytes.fromhex(key_hex)
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        dec = cipher.decrypt(ciphertext)
        magic = dec[40:44]
        if magic == b"GDPC":
            print(f"FOUND KEY (CBC)! Key (hex): {key_hex}")
            break
    except Exception as e:
        pass
