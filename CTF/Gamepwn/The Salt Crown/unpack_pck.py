import struct
import os

def unpack_pck(pck_path, out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    with open(pck_path, "rb") as f:
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
        for _ in range(file_count):
            path_len = struct.unpack("<I", f.read(4))[0]
            path_data = f.read(path_len)
            path = path_data.decode("utf-8", errors="ignore").rstrip("\x00")
            
            # Align read pointer to 4 bytes
            pad = (4 - (path_len % 4)) % 4
            f.read(pad)
            
            offset = struct.unpack("<Q", f.read(8))[0]
            size = struct.unpack("<Q", f.read(8))[0]
            md5 = f.read(16)
            
            flags = 0
            if pack_format >= 2:
                flags = struct.unpack("<I", f.read(4))[0]
                
            files.append((path, offset, size, flags))
            
        print(f"Extracting {file_count} files...")
        for path, offset, size, flags in files:
            # Clean path name (remove res:// prefix)
            clean_path = path
            if clean_path.startswith("res://"):
                clean_path = clean_path[6:]
                
            # Avoid directory traversal attacks
            clean_path = clean_path.replace("..", "__")
            target_path = os.path.join(out_dir, clean_path)
            
            # Ensure target folder exists
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            # Read from PCK and write to target
            f.seek(offset)
            file_data = f.read(size)
            
            with open(target_path, "wb") as out_f:
                out_f.write(file_data)
                
        print("Unpacking complete!")

if __name__ == "__main__":
    if os.path.exists("decrypted_game.pck"):
        unpack_pck("decrypted_game.pck", "extracted_pck")
    else:
        print("decrypted_game.pck does not exist yet.")
