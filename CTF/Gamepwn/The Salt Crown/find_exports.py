import pefile

pe = pefile.PE("challenge_core.windows.template_release.x86_64.dll")

print("Exported symbols:")
if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
    for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        name = exp.name.decode() if exp.name else "ordinal " + str(exp.ordinal)
        vaddr = exp.address
        print(f"  Name: {name}, Address: {hex(vaddr)}")
else:
    print("No exports found in PE directory.")
