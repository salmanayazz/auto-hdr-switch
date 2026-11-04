"""Windows HDR (advanced color) control via the DisplayConfig API."""
import ctypes
import sys
from ctypes import wintypes

QDC_ONLY_ACTIVE_PATHS = 2
GET_ADVANCED_COLOR_INFO = 9
SET_ADVANCED_COLOR_STATE = 10

PATH_SIZE = 72
MODE_SIZE = 64


class LUID(ctypes.Structure):
    _fields_ = [("Low", wintypes.DWORD), ("High", wintypes.LONG)]


class Header(ctypes.Structure):
    _fields_ = [("type", wintypes.UINT), ("size", wintypes.UINT),
                ("adapterId", LUID), ("id", wintypes.UINT)]


class ColorInfo(ctypes.Structure):
    _fields_ = [("header", Header), ("value", wintypes.UINT),
                ("colorEncoding", wintypes.UINT), ("bitsPerColorChannel", wintypes.UINT)]


class ColorState(ctypes.Structure):
    _fields_ = [("header", Header), ("enable", wintypes.UINT)]


_user32 = ctypes.windll.user32


def _targets():
    """Yield (adapterId LUID, target id) for each active display path."""
    np_, nm = wintypes.UINT(), wintypes.UINT()
    if _user32.GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, ctypes.byref(np_), ctypes.byref(nm)):
        return
    paths = (ctypes.c_ubyte * (PATH_SIZE * np_.value))()
    modes = (ctypes.c_ubyte * (MODE_SIZE * nm.value))()
    if _user32.QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS, ctypes.byref(np_), paths,
                                  ctypes.byref(nm), modes, None):
        return
    for i in range(np_.value):
        base = i * PATH_SIZE + 20  # targetInfo starts after sourceInfo (20 bytes)
        luid = LUID.from_buffer_copy(bytes(paths[base:base + 8]))
        tid = int.from_bytes(bytes(paths[base + 8:base + 12]), "little")
        yield luid, tid


def _info(luid, tid):
    ci = ColorInfo()
    ci.header = Header(GET_ADVANCED_COLOR_INFO, ctypes.sizeof(ColorInfo), luid, tid)
    if _user32.DisplayConfigGetDeviceInfo(ctypes.byref(ci)):
        return None
    return ci.value


def displays():
    """List of (luid, id, supported, enabled) for each active display."""
    out = []
    for luid, tid in _targets():
        v = _info(luid, tid)
        if v is not None:
            out.append((luid, tid, bool(v & 1), bool(v & 2)))
    return out


def is_supported():
    return any(d[2] for d in displays())


def is_enabled():
    """True if any HDR-capable display currently has HDR on."""
    return any(d[3] for d in displays())


def set_hdr(on):
    """Set HDR on every HDR-capable display. Returns True if anything changed."""
    changed = False
    for luid, tid, supported, enabled in displays():
        if supported and enabled != on:
            cs = ColorState()
            cs.header = Header(SET_ADVANCED_COLOR_STATE, ctypes.sizeof(ColorState), luid, tid)
            cs.enable = int(on)
            changed |= _user32.DisplayConfigSetDeviceInfo(ctypes.byref(cs)) == 0
    return changed


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if cmd == "--on":
        set_hdr(True)
    elif cmd == "--off":
        set_hdr(False)
    print([(d[1], "supported" if d[2] else "no-hdr", "on" if d[3] else "off") for d in displays()])
