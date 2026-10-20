"""OKLCH, and the conversion the surface layer is derived in.

A perceptual colour space, so that a lightness step is a step anybody can
see. sRGB is not that: a mix of two colours in sRGB does not move the
lightness evenly, and the hue does not survive the trip.

The package's neutrals are cool. That is not an accident of the hexes:
they all sit at the hue of anthracite, with a chroma that rises as they get
lighter. Deriving the neutrals in OKLCH keeps that, where a mix in sRGB
would neutralise it — mixing a cool colour toward a warm one passes through
grey on the way.

The formulas are the published ones (Bjorn Ottosson), and the conversion
back to sRGB is the inverse, with the usual gamut clamp.
"""

import math


def srgb_to_linear(channel: float) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear_to_srgb(channel: float) -> int:
    c = max(0.0, min(1.0, channel))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return round(v * 255)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(rgb)


def rgb_to_oklch(rgb) -> tuple[float, float, float]:
    r, g, b = (srgb_to_linear(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (x ** (1 / 3) if x > 0 else 0.0 for x in (l, m, s))
    lightness = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    chroma = math.hypot(a, bb)
    hue = math.degrees(math.atan2(bb, a)) % 360
    return lightness, chroma, hue


def oklch_to_rgb(lightness: float, chroma: float, hue: float) -> tuple[int, int, int]:
    h = math.radians(hue)
    a = chroma * math.cos(h)
    b = chroma * math.sin(h)
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = (x ** 3 if x > 0 else 0.0 for x in (l_, m_, s_))
    r = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return (linear_to_srgb(r), linear_to_srgb(g), linear_to_srgb(bb))


def relative_luminance(rgb) -> float:
    """The WCAG relative luminance of a colour."""
    r, g, b = (srgb_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(first, second) -> float:
    """The WCAG contrast ratio between two colours, 1 to 21."""
    a = relative_luminance(first)
    b = relative_luminance(second)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)
