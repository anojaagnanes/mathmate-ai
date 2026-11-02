"""Mia new look: longer hair + professional-dress repaint, rebuilt from teacher.glb.

Rebuildable: `python3 scripts/mia_look.py` (run from repo root).
Reads  frontend/public/models/mia/teacher.glb
Writes frontend/public/models/mia/teacher.glb (same rig, morphs, skinning)
Rollback: `git checkout -- frontend/public/models/mia/teacher.glb`
"""
import json
import struct
import sys
import zlib

GLB = 'frontend/public/models/mia/teacher.glb'

# ---------------------------------------------------------------- PNG codec
def png_decode(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, w = 8, None
    raw = b''
    while pos < len(data):
        (ln,) = struct.unpack('>I', data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, bd, ct, comp, filt, inter = struct.unpack('>IIBBBBB', chunk)
            assert bd == 8 and inter == 0, (bd, inter)
            ch = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
        elif typ == b'IDAT':
            raw += chunk
        elif typ == b'IEND':
            break
        pos += 12 + ln
    px = zlib.decompress(raw)
    stride = w * ch
    out = bytearray(w * h * ch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = px[p]
        p += 1
        line = bytearray(px[p:p + stride])
        p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, ch, out


def png_encode(w, h, ch, out):
    stride = w * ch
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += out[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)
    ctype = {1: 0, 3: 2, 4: 6}[ch]
    ihdr = struct.pack('>IIBBBBB', w, h, 8, ctype, 0, 0, 0)

    def ck(typ, payload):
        return struct.pack('>I', len(payload)) + typ + payload + struct.pack('>I', zlib.crc32(typ + payload))
    return b'\x89PNG\r\n\x1a\n' + ck(b'IHDR', ihdr) + ck(b'IDAT', comp) + ck(b'IEND', b'')


# ---------------------------------------------------------------- GLB helpers
def load_glb(path):
    raw = bytearray(open(path, 'rb').read())
    magic, ver, ln = struct.unpack('<III', raw[:12])
    assert magic == 0x46546C67 and ver == 2
    (clen,) = struct.unpack('<I', raw[12:16])
    assert raw[16:20] == b'JSON'
    js = json.loads(raw[20:20 + clen])
    boff = 20 + clen
    (blen,) = struct.unpack('<I', raw[boff:boff + 4])
    assert raw[boff + 4:boff + 8] == b'BIN\x00'
    return js, bytes(raw[boff + 8:boff + 8 + blen])


def acc_data(js, bindata, idx, kind):
    acc = js['accessors'][idx]
    bv = js['bufferViews'][acc['bufferView']]
    assert bv.get('byteStride', 0) in (0,), bv
    comp = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    assert acc['componentType'] == 5126, acc
    n = acc['count'] * comp
    start = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
    return acc, bv, start, list(struct.unpack(f'<{n}f', bindata[start:start + n * 4]))


def put_floats(bindata, start, vals):
    bindata[start:start + len(vals) * 4] = struct.pack(f'<{len(vals)}f', *vals)


# ---------------------------------------------------------------- main
def main():
    js, bindata = load_glb(GLB)
    bindata = bytearray(bindata)
    mesh = js['meshes'][0]
    assert len(mesh['primitives']) == 3, 'unexpected mesh layout'

    # ---- 1. long hair: stretch back-hair verts downward (prim 2) ----
    hair = mesh['primitives'][2]
    p_acc, p_bv, p_start, pos = acc_data(js, bindata, hair['attributes']['POSITION'], 'pos')
    n_acc, n_bv, n_start, nor = acc_data(js, bindata, hair['attributes']['NORMAL'], 'nor')
    assert p_acc['count'] == 596, p_acc['count']
    ia = js['accessors'][hair['indices']]
    ibv = js['bufferViews'][ia['bufferView']]
    assert ia['componentType'] in (5123, 5125), ia
    fmt = '<H' if ia['componentType'] == 5123 else '<I'
    isz = 2 if ia['componentType'] == 5123 else 4
    istart = ibv.get('byteOffset', 0) + ia.get('byteOffset', 0)
    idx = list(struct.unpack(f'<{ia["count"]}{fmt[1]}', bindata[istart:istart + ia['count'] * isz]))

    moved = 0
    for i in range(p_acc['count']):
        x, y, z = pos[3 * i:3 * i + 3]
        if y < 1.62:
            depth = min(max((0.0 - z) / 0.08, 0.0), 1.0)  # 0 front -> 1 deep back
            s = 1.0 + (2.0 - 1.0) * (depth * depth * (3 - 2 * depth))
            if s > 1.001:
                pos[3 * i + 1] = 1.62 - (1.62 - y) * s
                moved += 1
    print(f'hair verts moved: {moved} of {p_acc["count"]}')
    # recompute area-weighted normals for the hair mesh
    acc_n = [0.0] * (p_acc['count'] * 3)
    for t in range(0, len(idx), 3):
        a, b, c = idx[t:t + 3]
        ax, ay, az = pos[3 * a:3 * a + 3]
        bx, by, bz = pos[3 * b:3 * b + 3]
        cx, cy, cz = pos[3 * c:3 * c + 3]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        for v in (a, b, c):
            acc_n[3 * v] += nx
            acc_n[3 * v + 1] += ny
            acc_n[3 * v + 2] += nz
    for i in range(p_acc['count']):
        nx, ny, nz = acc_n[3 * i:3 * i + 3]
        ln = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        nor[3 * i:3 * i + 3] = [nx / ln, ny / ln, nz / ln]
    put_floats(bindata, p_start, pos)
    put_floats(bindata, n_start, nor)
    xs = pos[0::3]
    ys = pos[1::3]
    zs = pos[2::3]
    p_acc['min'] = [min(xs), min(ys), min(zs)]
    p_acc['max'] = [max(xs), max(ys), max(zs)]
    print('hair bounds now: min', [round(v, 3) for v in p_acc['min']], 'max', [round(v, 3) for v in p_acc['max']])
    # morph deltas on hair must be ~zero (face morphs should not move hair)
    worst = 0.0
    for tgt in hair.get('targets', []):
        if 'bufferView' not in js['accessors'][tgt['POSITION']]:
            continue  # zero-filled: morph does not move hair
        _, _, _, vals = acc_data(js, bindata, tgt['POSITION'], 'm')
        worst = max(worst, max((abs(v) for v in vals), default=0.0))
    print('hair morph max abs delta:', round(worst, 6))

    # ---- 2. professional dress: repaint body color texture ----
    img = next(im for im in js['images'] if im.get('name') == 'f007_body_color')
    bv = js['bufferViews'][img['bufferView']]
    start = bv.get('byteOffset', 0)
    w, h, ch, px = png_decode(bytes(bindata[start:start + bv['byteLength']]))
    assert (w, h, ch) == (512, 512, 3), (w, h, ch)
    w2, h2, ch2, px2 = png_decode(png_encode(w, h, ch, px))
    assert (w2, h2, ch2) == (w, h, ch) and bytes(px2) == bytes(px), 'PNG codec round-trip failed'
    print('PNG codec round-trip OK')

    def lum(r, g, b):
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def paint(r, g, b, target):
        li, lt = lum(r, g, b), lum(*target)
        s = (li / lt) if lt > 1 else 1.0
        return tuple(max(0, min(255, int(c * s))) for c in target)

    NAVY, CHARCOAL, BLACKBROWN, WHITE = (44, 58, 86), (52, 55, 62), (32, 27, 25), (238, 232, 222)
    counts = dict(navy=0, charcoal=0, shoes=0, blouse=0, skin_kept=0, kept=0)

    def in_box(x, y, x0, y0, x1, y1):
        return x0 <= x <= x1 and y0 <= y <= y1

    def is_skin(r, g, b, tot):
        return (tot > 380 and r >= g >= b) or (r > 110 and r > g + 15 and g > b + 5)

    HANDS = [(0, 0, 115, 155), (395, 0, 511, 155)]
    BLOUSE = (225, 120, 285, 308)
    JACKET = [(140, 0, 370, 342), (12, 20, 168, 278), (342, 20, 498, 278)]
    JEANS = [(5, 330, 145, 438), (365, 330, 505, 438), (140, 342, 370, 400)]
    BOOTS = [(40, 438, 160, 511), (350, 438, 470, 511)]

    def is_brass(r, g, b, tot):
        return r > 140 and g > 100 and b < 110 and r - b > 50 and tot > 300
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            r, g, b = px[i], px[i + 1], px[i + 2]
            tot = r + g + b
            if tot < 25:
                continue  # unmapped background
            if any(in_box(x, y, *bx) for bx in HANDS) or is_skin(r, g, b, tot):
                counts['skin_kept'] += 1
                continue
            if in_box(x, y, *BLOUSE):
                if r > b + 25 and r > g + 10 and tot > 80:
                    px[i:i + 3] = bytes(paint(r, g, b, WHITE))
                    counts['blouse'] += 1
                else:
                    px[i:i + 3] = bytes(paint(r, g, b, NAVY))
                    counts['navy'] += 1
            elif any(in_box(x, y, *bx) for bx in JACKET):
                if is_brass(r, g, b, tot):
                    counts['kept'] += 1
                else:
                    px[i:i + 3] = bytes(paint(r, g, b, NAVY))
                    counts['navy'] += 1
            elif any(in_box(x, y, *bx) for bx in JEANS):
                px[i:i + 3] = bytes(paint(r, g, b, CHARCOAL))
                counts['charcoal'] += 1
            elif any(in_box(x, y, *bx) for bx in BOOTS):
                px[i:i + 3] = bytes(paint(r, g, b, BLACKBROWN))
                counts['shoes'] += 1
            else:
                counts['kept'] += 1
    print('repaint counts:', counts)
    new_png = png_encode(w, h, ch, px)
    open('/tmp/mia_tex/repainted_body.png', 'wb').write(new_png)

    # ---- 3. rebuild GLB (only offsets/sizes change; structure identical) ----
    new_views = {}
    for i, v in enumerate(js['bufferViews']):
        s = v.get('byteOffset', 0)
        new_views[i] = bindata[s:s + v['byteLength']]
    new_views[img['bufferView']] = new_png
    out = bytearray()
    for i, v in enumerate(js['bufferViews']):
        while len(out) % 4:
            out.append(0)
        v['byteOffset'] = len(out)
        out += new_views[i]
        v['byteLength'] = len(new_views[i])
    js['buffers'][0]['byteLength'] = len(out)
    blob = json.dumps(js, separators=(',', ':')).encode('utf-8')
    while len(blob) % 4:
        blob += b' '
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(blob) + 8 + len(out) + (-len(out) % 4))
    glb += struct.pack('<I', len(blob)) + b'JSON' + blob
    glb += struct.pack('<I', len(out) + (-len(out) % 4)) + b'BIN\x00' + bytes(out) + b'\x00' * (-len(out) % 4)
    open(GLB, 'wb').write(glb)
    print('wrote', GLB, len(glb), 'bytes')

    # ---- 4. validate by re-parsing ----
    js2, bin2 = load_glb(GLB)
    assert [m['name'] for m in js2['materials']] == ['f007_body', 'f007_head', 'f007_opacity']
    assert js2['meshes'][0]['extras']['targetNames'] == js['meshes'][0]['extras']['targetNames']
    assert len(js2['accessors']) == len(js['accessors']) and len(js2['skins'][0]['joints']) == 80
    for v in js2['bufferViews']:
        assert v['byteOffset'] + v['byteLength'] <= len(bin2)
    w2, h2, ch2, _ = png_decode(bytes(bin2[js2['bufferViews'][img['bufferView']]['byteOffset']:][:js2['bufferViews'][img['bufferView']]['byteLength']]))
    assert (w2, h2, ch2) == (512, 512, 3)
    print('reparse OK: structure identical, textures valid')


if __name__ == '__main__':
    sys.exit(main())
