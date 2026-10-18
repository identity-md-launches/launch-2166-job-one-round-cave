#!/usr/bin/env python3
"""Create a 512px baseline JPEG from an RGB8 PNG using only the standard library.

Small build utility, not a general image decoder. Rejects unsupported PNG forms.
No packages, network, external executables, metadata or configuration access.
"""
import argparse
import math
from pathlib import Path
import struct
import zlib

ZIG = [0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,
       12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,
       35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,
       58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63]
Q = [16,11,10,16,24,40,51,61,12,12,14,19,26,58,60,55,
     14,13,16,24,40,57,69,56,14,17,22,29,51,87,80,62,
     18,22,37,56,68,109,103,77,24,35,55,64,81,104,113,92,
     49,64,78,87,103,121,120,101,72,92,95,98,112,100,103,99]
COS = [[math.cos((2*x+1)*u*math.pi/16) * (1/math.sqrt(2) if u == 0 else 1)
        for x in range(8)] for u in range(8)]


def decode_png(path):
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not PNG")
    pos, compressed, header = 8, bytearray(), None
    while pos < len(data):
        length = struct.unpack_from(">I", data, pos)[0]
        kind, payload = data[pos+4:pos+8], data[pos+8:pos+8+length]
        crc = struct.unpack_from(">I", data, pos+8+length)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("bad PNG chunk CRC")
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        if kind == b"IDAT":
            compressed.extend(payload)
        pos += length + 12
        if kind == b"IEND":
            break
    if header is None:
        raise ValueError("missing PNG header")
    w, h, depth, color, compression, filtering, interlace = header
    if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError("only noninterlaced RGB8 PNG is supported")
    raw = zlib.decompress(compressed)
    stride = 3*w
    if len(raw) != (stride+1)*h:
        raise ValueError("bad PNG scanline size")
    rows, previous = [], bytearray(stride)
    for y in range(h):
        start = y*(stride+1)
        mode = raw[start]
        row = bytearray(raw[start+1:start+stride+1])
        for x in range(stride):
            a = row[x-3] if x >= 3 else 0
            b = previous[x]
            c = previous[x-3] if x >= 3 else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = a
            elif mode == 2:
                predictor = b
            elif mode == 3:
                predictor = (a+b)//2
            elif mode == 4:
                p = a+b-c
                da, db, dc = abs(p-a), abs(p-b), abs(p-c)
                predictor = a if da <= db and da <= dc else b if db <= dc else c
            else:
                raise ValueError("unknown PNG filter")
            row[x] = (row[x]+predictor) & 255
        rows.append(row)
        previous = row
    return w, h, rows


def resize(w, h, rows, size=512):
    """Bilinear sample RGB pixels at output pixel centers."""
    output = []
    for y in range(size):
        sy = max(0, min(h-1, (y+0.5)*h/size-0.5))
        ya, yb = int(sy), min(h-1, int(sy)+1)
        fy = sy-ya
        row = []
        for x in range(size):
            sx = max(0, min(w-1, (x+0.5)*w/size-0.5))
            xa, xb = int(sx), min(w-1, int(sx)+1)
            fx = sx-xa
            pixel = []
            for channel in range(3):
                a = rows[ya][3*xa+channel]*(1-fx)+rows[ya][3*xb+channel]*fx
                b = rows[yb][3*xa+channel]*(1-fx)+rows[yb][3*xb+channel]*fx
                pixel.append(a*(1-fy)+b*fy)
            row.append(pixel)
        output.append(row)
    return output


def dct(block):
    temp = [[sum(block[y][x]*COS[u][x] for x in range(8)) for u in range(8)]
            for y in range(8)]
    return [sum(temp[y][u]*COS[v][y] for y in range(8))/4
            for v in range(8) for u in range(8)]


def blocks(pixels):
    for by in range(0, len(pixels), 8):
        for bx in range(0, len(pixels), 8):
            planes = [[[0]*8 for _ in range(8)] for _ in range(3)]
            for y in range(8):
                for x in range(8):
                    r, g, b = pixels[by+y][bx+x]
                    planes[0][y][x] = .299*r+.587*g+.114*b-128
                    planes[1][y][x] = -.168736*r-.331264*g+.5*b
                    planes[2][y][x] = .5*r-.418688*g-.081312*b
            yield [dct(p) for p in planes]


def jpeg(coefficients, size, quality):
    scale = 5000/quality if quality < 50 else 200-2*quality
    quant = [max(1, min(255, int((q*scale+50)//100))) for q in Q]
    out = bytearray(b"\xff\xd8")

    def marker(code, payload):
        out.extend(bytes([255, code])+struct.pack(">H", len(payload)+2)+payload)

    marker(0xe0, b"JFIF\0\x01\x01\0\0\x01\0\x01\0\0")
    marker(0xdb, bytes([0]+[quant[i] for i in ZIG]))
    marker(0xc0, bytes([8])+struct.pack(">HH", size, size)+bytes([3,1,0x11,0,2,0x11,0,3,0x11,0]))
    # Incomplete canonical codes are legal; no code consists solely of ones.
    dc_symbols = list(range(12))
    ac_symbols = [0, 0xf0]+[16*run+bits for run in range(16) for bits in range(1,11)]
    marker(0xc4, bytes([0]+[0,0,0,12]+[0]*12+dc_symbols))
    marker(0xc4, bytes([0x10]+[0]*7+[len(ac_symbols)]+[0]*8+ac_symbols))
    dc = {symbol: (i,4) for i,symbol in enumerate(dc_symbols)}
    ac = {symbol: (i,8) for i,symbol in enumerate(ac_symbols)}
    marker(0xda, bytes([3,1,0,2,0,3,0,0,63,0]))
    accumulator, available = 0, 0

    def bits(value, width):
        nonlocal accumulator, available
        accumulator = (accumulator << width) | value
        available += width
        while available >= 8:
            available -= 8
            byte = (accumulator >> available) & 255
            out.append(byte)
            if byte == 255:
                out.append(0)
        accumulator &= (1 << available)-1

    def number(value):
        width = abs(value).bit_length()
        return width, value if value >= 0 else value+(1 << width)-1

    previous = [0,0,0]
    for triple in coefficients:
        for channel, block in enumerate(triple):
            q = [round(block[i]/quant[i]) for i in ZIG]
            width, value = number(q[0]-previous[channel])
            bits(*dc[width]); bits(value, width)
            previous[channel] = q[0]
            zeros = 0
            for coefficient in q[1:]:
                if coefficient == 0:
                    zeros += 1
                    continue
                while zeros >= 16:
                    bits(*ac[0xf0]); zeros -= 16
                width, value = number(coefficient)
                bits(*ac[16*zeros+width]); bits(value, width)
                zeros = 0
            if zeros:
                bits(*ac[0])
    if available:
        bits((1 << (8-available))-1, 8-available)
    out.extend(b"\xff\xd9")
    return bytes(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("png")
    parser.add_argument("jpg")
    args = parser.parse_args()
    root = Path.cwd().resolve()
    for path in (args.png, args.jpg):
        if not Path(path).resolve().is_relative_to(root):
            parser.error("image paths must resolve inside the current workspace")
    w, h, rows = decode_png(args.png)
    if w != h:
        parser.error("wall must be square")
    coefficients = list(blocks(resize(w, h, rows)))
    for quality in (65,50,40,30,20,10):
        data = jpeg(coefficients, 512, quality)
        if len(data) < 100_000:
            Path(args.jpg).write_bytes(data)
            print(f"{w}x{h} RGB8 PNG -> 512x512 baseline JPEG, {len(data)} bytes, quality {quality}")
            return
    parser.error("preview exceeds 100 KB")


if __name__ == "__main__":
    main()
