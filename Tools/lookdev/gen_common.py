"""FrontRooms surface textures.

Every map is seamless (spectral noise is periodic by construction, drawn features
wrap with modulo coordinates). Physical repeats divide the stream's 256 m rebase so
world-projected UVs never jump when the origin shifts:
  wallpaper 256/373 m wide (one 27" roll), carpet 1 m, ceiling 256/210 m (one 4' run
  of two 2'x4' tiles), macro 8 m.
Outputs: <name>_A.png (sRGB albedo, alpha unused), <name>_N.png (linear, OpenGL +Y
normal), <name>_S.png (linear: R smoothness, G cavity/AO, B wet mask, A unused).
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

OUT = sys.argv[1]
REF = sys.argv[2]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261001)


def spectral(h, w, beta, seed, fmin=1.0):
    """Periodic 1/f^beta noise normalised to 0..1."""
    r = np.random.default_rng(seed)
    white = r.standard_normal((h, w))
    F = np.fft.fft2(white)
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    amp = 1.0 / np.power(np.maximum(f, fmin), beta)
    amp[0, 0] = 0.0
    n = np.real(np.fft.ifft2(F * amp))
    n -= n.min(); n /= max(1e-8, n.max())
    return n.astype(np.float32)


def band(h, w, lo, hi, seed):
    """Periodic band-limited noise between lo and hi cycles per tile."""
    r = np.random.default_rng(seed)
    F = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    f = np.sqrt(fx * fx + fy * fy)
    mask = np.exp(-((np.log(np.maximum(f, 1e-3)) - np.log((lo * hi) ** .5)) ** 2) / (2 * (np.log(hi / lo) / 2.5) ** 2))
    mask[0, 0] = 0
    n = np.real(np.fft.ifft2(F * mask))
    n -= n.min(); n /= max(1e-8, n.max())
    return n.astype(np.float32)


def blur(img, sigma):
    """Periodic gaussian blur via FFT."""
    h, w = img.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    if img.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(img) * g)).astype(np.float32)
    return np.stack([blur(img[..., c], sigma) for c in range(img.shape[2])], -1)


def normal_from_height(hgt, strength):
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * .5
    drow = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * .5
    nx = -dx * strength
    ny = drow * strength  # v (up) runs against image rows
    nz = np.ones_like(hgt)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return n


def save_rgb(path, rgb):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + .5).astype(np.uint8), "RGB").save(path, optimize=True)


def save_rgba(path, rgba):
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + .5).astype(np.uint8), "RGBA").save(path, optimize=True)


def save_normal(path, n):
    save_rgb(path, n * .5 + .5)


def srgb_to_lin(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)


def hexc(s):
    return np.array([int(s[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def resize(arr, w, h):
    im = Image.fromarray((np.clip(arr, 0, 1) * 65535).astype(np.uint16) if arr.ndim == 2 else (np.clip(arr, 0, 1) * 255).astype(np.uint8))
    im = im.resize((w, h), Image.LANCZOS)
    out = np.asarray(im).astype(np.float32)
    return out / (65535 if arr.ndim == 2 else 255)


