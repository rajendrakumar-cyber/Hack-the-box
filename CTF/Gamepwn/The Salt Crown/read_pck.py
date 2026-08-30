import struct

def parse_pck(filename):
    with open(filename, "rb") as f:
        # Read header
        magic = f.read(4)
        if magic != b"GDPC":
            print(f"Invalid magic: {magic}")
            return
        
        pack_format = struct.unpack("<I", f.read(4))[0]
        version_major = struct.unpack("<I", f.read(4))[0]
        version_minor = struct.unpack("<I", f.read(4))[0]
        version_revision = struct.unpack("<I", f.read(4))[0]
        
        f.read(16) # reserved
        
        file_count = struct.unpack("<I", f.read(4))[0]
        print(f"Format: {pack_format}, Version: {version_major}.{version_minor}.{version_revision}, Files: {file_count}")
        
        files = []
        for i in range(file_count):
            path_len = struct.unpack("<I", f.read(4))[0]
            # Path is null-padded to 4 bytes boundary in Godot
            # Actually, let's read the path.
            # In Godot, the path is stored as path_len bytes, but in Godot 3/4 it is padded to 4 bytes.
            # Let's check how the padding works.
            # Usually: path_padded_len = (path_len + 3) & ~3 (aligned to 4 bytes)
            # Let's verify by checking if the next read works.
            path_data = f.read(path_len)
            path = path_data.decode("utf-8", errors="ignore").rstrip("\x00")
            
            # Read padding if any
            pad = (4 - (path_len % 4)) % 4
            f.read(pad)
            
            offset = struct.unpack("<Q", f.read(8))[0]
            size = struct.unpack("<Q", f.read(8))[0]
            md5 = f.read(16)
            
            # In Godot 4, there are flags (4 bytes)
            flags = struct.unpack("<I", f.read(4))[0]
            
            files.append((path, offset, size, flags))
            
        for path, offset, size, flags in files[:100]:
            print(f"File: {path}, Size: {size} bytes, Offset: {offset}, Flags: {flags}")
            
        if len(files) > 100:
            print(f"... and {len(files) - 100} more files.")

if __name__ == "__main__":
    parse_pck("game.pck")
