import random
import colorsys


def hex_to_rgb(hex_color):
    """ Convert hex color (6-digit) to rgb tuple """
    if hex_color is None:
        return None
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = hex_color[0] + hex_color[0] + hex_color[1] + hex_color[1] + hex_color[2] + hex_color[2]
    if len(hex_color) > 6:
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color):
    """ Convert rgb tuple to hex string """
    return f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"


def get_luminance(rgb_color):
    """ 
    Relative luminance of an RGB color
    0 for black
    1 for white
    """
    r, g, b = [x / 255.0 for x in rgb_color]
    
    # Apply sRGB linearization
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4

    # Calculate luminance with standard coefficients
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return luminance


def hex_luminance(hex_color):
    if hex_color is None:
        return None
    return get_luminance(hex_to_rgb(hex_color))


def contrast_ratio(rgb1, rgb2):
    l1 = get_luminance(rgb1)
    l2 = get_luminance(rgb2)
    # Ensure L1 is brighter than L2
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def hex_contrast_ratio(hex1, hex2):
    return contrast_ratio(hex_to_rgb(hex1), hex_to_rgb(hex2))


def generate_random_rgb():
    return tuple((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))


def generate_contrasting_color(reference_colors_hex: list, min_contrast_ratio=4.5, max_tries=1000, prohibited_colors=[]):
    """
    Generate a random hex color with a minimum contrast ratio against a set of reference colors

    Args:
        reference_colors_hex: A list of hex colors in #RRGGBB format
        min_contrast_ratio: Minimum required contrast ratio. Defaults to 4.5 (WCAG AA)
        max_tries: Maximum attempts to find a suitable color
    """
    if len(reference_colors_hex) < 1:
        return generate_random_rgb()

    reference_rgbs = [hex_to_rgb(i) for i in reference_colors_hex]
    
    for _ in range(max_tries):
        random_rgb = generate_random_rgb()
        random_hex = rgb_to_hex(random_rgb)
        if random_hex not in prohibited_colors:
            result = True
            for i in reference_rgbs:
                ratio = contrast_ratio(i, random_rgb)
                if ratio < min_contrast_ratio:
                    result = False
            if result:
                return random_hex  
        
    return None


def adjust_for_contrast(reference_hex, target_ratio=3, prohibited_outputs=[], direction=0):
    """
    Adjusts lightness of a hex color
    """
    if reference_hex is None:
        return None
    reference_rgb = hex_to_rgb(reference_hex)
    r, g, b = [x / 255.0 for x in reference_rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    fitment = reference_rgb
    for i in range(101):
        if get_luminance(reference_rgb) > 0.5 or direction == -1:
            new_l = l - (i / 100)
        else:
            new_l = l + (i / 100)
        new_l = max(0, min(1, new_l))
        rgb_floats = colorsys.hls_to_rgb(h, new_l, s)
        rgb = tuple(int(x * 255) for x in rgb_floats)

        if contrast_ratio(reference_rgb, rgb) >= target_ratio:
            hex_value = rgb_to_hex(rgb)
            if hex_value not in prohibited_outputs:
                return hex_value
    hex_value = rgb_to_hex(rgb)
    if hex_value not in prohibited_outputs:
        return hex_value
    return reference_hex

