"""Experimental Syrian Warfare v1.2.1.53 normal camera patch. Python 3."""
from pathlib import Path
import argparse, hashlib, struct, os, tempfile

OriginalHash = 'e53501ff6180c496532c085bb888f7ef3b56587f176feaf30c402e61eed3b5d7'
Bindings = [(0x92F9A, 4, 0x1010B294, 0x1010C64C, b'a'),
            (0x9302B, 5, 0x1010B29C, 0x1010C654, b'd'),
            (0x930BC, 2, 0x1010B7E8, 0x1010C700, b'w'),
            (0x9314D, 4, 0x1010B7EC, 0x1010C6E0, b's')]

def Digest(Data):
    return hashlib.sha256(Data).hexdigest()

def Build(Data):
    if Digest(Data) != OriginalHash:
        raise ValueError('Original DLL hash mismatch; refusing to patch.')
    Result = bytearray(Data)
    for Rva, Length, OldPtr, NewPtr, Key in Bindings:
        Offset = Rva - 0x1000 + 0x400 - 2
        Expected = bytes([0x6A, Length, 0x68]) + struct.pack('<I', OldPtr)
        if Data[Offset:Offset+7] != Expected:
            raise ValueError(f'Unexpected instructions at RVA {Rva:X}.')
        StringOffset = NewPtr - 0x10104000 + 0x102A00
        if Data[StringOffset:StringOffset+2] != Key + b'\0':
            raise ValueError('Replacement string mismatch.')
        Result[Offset:Offset+7] = b'\x6A\x01\x68' + struct.pack('<I', NewPtr)
    return bytes(Result)

def AtomicWrite(Pathname, Data):
    Fd, Temp = tempfile.mkstemp(prefix='sw_camera_', dir=Pathname.parent)
    try:
        with os.fdopen(Fd, 'wb') as File:
            File.write(Data); File.flush(); os.fsync(File.fileno())
        os.replace(Temp, Pathname)
    finally:
        if os.path.exists(Temp): os.unlink(Temp)

EdgeOffset = 0x93BA8 - 0x1000 + 0x400

def BuildState(Original, Wasd=False, EdgeEnabled=True):
    Patched = Build(Original)
    if Original[EdgeOffset-4:EdgeOffset+6] != bytes.fromhex('80 79 10 00 75 4c 66 0f 6e 5d'):
        raise ValueError('Unexpected edge scrolling instructions.')
    Result = Patched if Wasd else Original
    if not EdgeEnabled:
        Result = Result[:EdgeOffset] + b'\xeb' + Result[EdgeOffset+1:]
    return Result

def Detect(Current):
    # Reconstruct stock only at the known patch locations, then verify the entire file.
    Candidate = bytearray(Current)
    for Rva, Length, OldPtr, NewPtr, Key in Bindings:
        Offset = Rva - 0x1000 + 0x400 - 2
        Candidate[Offset:Offset+7] = bytes([0x6A, Length, 0x68]) + struct.pack('<I', OldPtr)
    Candidate[EdgeOffset:EdgeOffset+1] = b'\x75'
    Stock = bytes(Candidate)
    if Digest(Stock) != OriginalHash:
        raise ValueError('Unsupported game.dll version or unrelated modification. Native controls disabled.')
    for Wasd in (False, True):
        for EdgeEnabled in (False, True):
            if Current == BuildState(Stock, Wasd, EdgeEnabled):
                return Stock, Wasd, EdgeEnabled
    raise ValueError('Unrecognised or partial patch. Native controls disabled.')
