"""
Recplay 2.0 - Studio Icon & Logo Generator
Creates a brand-new, ultra-modern, high-fidelity application icon and logo for Recplay.
Features the exclusive "Quantum Rec-Play R" emblem:
- Deep obsidian glass squircle with dual chromatic neon rim lighting.
- Outer dynamic orbital energy loop (Electric Cyan -> Royal Cerulean -> Quantum Violet -> Neon Ruby).
- Geometric "R" Monogram fusing:
    1. Digital Cyber Pillar (left vertical stem)
    2. Studio Recording Aperture Lens with glowing Ruby REC core (upper loop)
    3. Forward Play Triangle (right leg pointing right ▶)
"""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def create_recplay_icon(size: int = 512) -> Image.Image:
    # 3x super-sampling for pristine sub-pixel anti-aliasing
    scale = 3
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))

    # 1. Outer App Squircle with Deep Obsidian Glass Gradient
    corner_radius = int(s * 0.22)
    bg = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)

    for y in range(s):
        ratio = y / float(s)
        # Deep obsidian slate (top #0B132B to bottom #040814)
        r = int(11 * (1 - ratio) + 4 * ratio)
        g = int(19 * (1 - ratio) + 7 * ratio)
        b = int(38 * (1 - ratio) + 16 * ratio)
        bg_draw.line([(0, y), (s, y)], fill=(r, g, b, 255))

    mask = Image.new("L", (s, s), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (s - 1, s - 1)], radius=corner_radius, fill=255)
    img.paste(bg, (0, 0), mask)

    draw = ImageDraw.Draw(img)

    # Multi-tone specular rim around squircle
    draw.rounded_rectangle(
        [(0, 0), (s - 1, s - 1)],
        radius=corner_radius,
        outline=(2, 132, 199, 210),
        width=int(s * 0.016),
    )
    draw.rounded_rectangle(
        [(int(s * 0.01), int(s * 0.01)), (s - 1 - int(s * 0.01), s - 1 - int(s * 0.01))],
        radius=corner_radius - int(s * 0.01),
        outline=(0, 240, 255, 90),
        width=int(s * 0.006),
    )

    cx, cy = s // 2, s // 2

    # 2. Glowing Ambient Neon Energy Bloom
    radius = int(s * 0.36)
    halo = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.ellipse(
        [(cx - radius - 30, cy - radius - 30), (cx + radius + 30, cy + radius + 30)],
        fill=(0, 240, 255, 45),
    )
    halo_draw.ellipse(
        [(cx - int(radius * 0.5), cy - int(radius * 0.5)), (cx + int(radius * 0.7), cy + int(radius * 0.7))],
        fill=(139, 92, 246, 50),
    )
    halo_draw.ellipse(
        [(cx - int(radius * 0.2), cy - int(radius * 0.2)), (cx + int(radius * 0.2), cy + int(radius * 0.2))],
        fill=(239, 68, 68, 65),
    )
    halo = halo.filter(ImageFilter.GaussianBlur(int(s * 0.05)))
    img = Image.alpha_composite(img, halo)
    draw = ImageDraw.Draw(img)

    # 3. Outer Continuous Orbital Energy Ring (Electric Cyan -> Cerulean -> Violet -> Ruby)
    ring_w = int(s * 0.055)
    arc_bbox = [(cx - radius, cy - radius), (cx + radius, cy + radius)]

    def lerp_color(c1, c2, t):
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

    col_cyan = (0, 240, 255, 255)
    col_blue = (14, 165, 233, 255)
    col_violet = (139, 92, 246, 255)
    col_ruby = (244, 63, 94, 255)

    start_deg = 25
    end_deg = 335
    span = end_deg - start_deg

    for deg in range(start_deg, end_deg):
        t = (deg - start_deg) / float(span)
        if t < 0.33:
            col = lerp_color(col_cyan, col_blue, t / 0.33)
        elif t < 0.66:
            col = lerp_color(col_blue, col_violet, (t - 0.33) / 0.33)
        else:
            col = lerp_color(col_violet, col_ruby, (t - 0.66) / 0.34)
        draw.arc(arc_bbox, start=deg, end=deg + 2, fill=col, width=ring_w)

    cap_r = ring_w // 2
    for angle_deg, color in [(start_deg, col_cyan), (end_deg, col_ruby)]:
        rad = math.radians(angle_deg)
        px = int(cx + radius * math.cos(rad))
        py = int(cy + radius * math.sin(rad))
        draw.ellipse([(px - cap_r, py - cap_r), (px + cap_r, py + cap_r)], fill=color)

    # 4. Central Geometric "R" Monogram (Rec + Play)
    # Balanced proportions
    stem_w = int(s * 0.082)
    stem_h = int(s * 0.44)
    stem_x = cx - int(s * 0.20)
    stem_y = cy - int(s * 0.22)

    # 4A. Left Stem with Rounded Ends & Neon Cyan/Blue Vertical Gradient
    stem_img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stem_img)
    for y_step in range(stem_y, stem_y + stem_h):
        t = (y_step - stem_y) / float(stem_h)
        c = lerp_color((0, 240, 255, 255), (14, 165, 233, 255), t)
        s_draw.line([(stem_x, y_step), (stem_x + stem_w, y_step)], fill=c)

    stem_mask = Image.new("L", (s, s), 0)
    sm_draw = ImageDraw.Draw(stem_mask)
    sm_draw.rounded_rectangle([(stem_x, stem_y), (stem_x + stem_w, stem_y + stem_h)], radius=int(stem_w * 0.38), fill=255)
    img.paste(stem_img, (0, 0), stem_mask)
    draw = ImageDraw.Draw(img)

    # 4B. Upper Loop of 'R' -> Circular Recording Lens
    loop_diam = int(stem_h * 0.54)
    loop_r = loop_diam // 2
    loop_cx = stem_x + stem_w + int(loop_r * 0.55)
    loop_cy = stem_y + loop_r

    # Loop body
    loop_bbox = [(loop_cx - loop_r, loop_cy - loop_r), (loop_cx + loop_r, loop_cy + loop_r)]
    draw.ellipse(loop_bbox, fill=(15, 23, 42, 255), outline=(0, 240, 255, 255), width=int(s * 0.016))

    # Top & middle horizontal connecting bridges to stem
    draw.rounded_rectangle([(stem_x + stem_w // 2, stem_y), (loop_cx, stem_y + int(stem_w * 0.72))], radius=4, fill=(0, 240, 255, 255))
    draw.rounded_rectangle([(stem_x + stem_w // 2, loop_cy + loop_r - int(stem_w * 0.72)), (loop_cx, loop_cy + loop_r)], radius=4, fill=(14, 165, 233, 255))

    # Glowing REC Core (Ruby Red Sphere inside upper loop)
    core_r = int(loop_r * 0.52)
    for cr in range(core_r, 0, -1):
        ratio = cr / float(core_r)
        r_c = int(255 * (1 - ratio * 0.15))
        g_c = int(35 * ratio)
        b_c = int(50 * ratio)
        draw.ellipse(
            [(loop_cx - cr, loop_cy - cr), (loop_cx + cr, loop_cy + cr)],
            fill=(r_c, g_c, b_c, 255),
        )
    # Bright specular lens gleam
    gl_r = max(2, int(core_r * 0.30))
    draw.ellipse(
        [(loop_cx - gl_r - 2, loop_cy - gl_r - 2), (loop_cx - 1, loop_cy - 1)],
        fill=(255, 255, 255, 230),
    )

    # 4C. Play Triangle (Right Leg of 'R' pointing forward ▶)
    # Beautiful equilateral right-pointing Play Arrow
    tri_h = int(s * 0.20)
    tri_w = int(tri_h * 0.95)
    tri_tip_x = cx + int(s * 0.23)
    tri_tip_y = stem_y + stem_h - int(tri_h * 0.45)

    p1 = (tri_tip_x, tri_tip_y)  # forward right tip
    p2 = (tri_tip_x - tri_w, tri_tip_y - tri_h // 2)  # top left
    p3 = (tri_tip_x - tri_w, tri_tip_y + tri_h // 2)  # bottom left

    # Outer neon cyan glow on play triangle
    draw.polygon([p1, p2, p3], fill=(0, 240, 255, 255))

    # Inner crisp white play arrow
    inset = int(s * 0.016)
    p1_in = (tri_tip_x - int(inset * 1.5), tri_tip_y)
    p2_in = (tri_tip_x - tri_w + inset, tri_tip_y - tri_h // 2 + int(inset * 0.86))
    p3_in = (tri_tip_x - tri_w + inset, tri_tip_y + tri_h // 2 - int(inset * 0.86))
    draw.polygon([p1_in, p2_in, p3_in], fill=(255, 255, 255, 255))

    # Downsample with Lanczos for smooth sub-pixel anti-aliasing
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    return final_img


def main():
    assets_dir = Path(__file__).resolve().parent
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. 512x512 Master PNG
    icon_512 = create_recplay_icon(512)
    png_path = assets_dir / "icon.png"
    icon_512.save(png_path, format="PNG")
    print(f"[OK] Generated {png_path}")

    # 2. Multi-size ICO for Windows Explorer & Taskbar
    ico_path = assets_dir / "icon.ico"
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icon_512.save(ico_path, format="ICO", sizes=sizes)
    print(f"[OK] Generated {ico_path}")

    # 3. Logo Banner
    banner_w, banner_h = 600, 160
    banner = Image.new("RGBA", (banner_w, banner_h), (8, 14, 28, 255))
    b_draw = ImageDraw.Draw(banner)

    small_icon = create_recplay_icon(110)
    banner.paste(small_icon, (25, 25), small_icon)

    try:
        font_large = ImageFont.truetype("arialbd.ttf", 64)
        font_small = ImageFont.truetype("segoeui.ttf", 20)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    b_draw.text((155, 30), "RECPLAY 2.0", fill=(0, 240, 255, 255), font=font_large)
    b_draw.text((158, 105), "AI Studio Screen Recorder & High-Fidelity Media Player", fill=(148, 163, 184, 255), font=font_small)

    banner_path = assets_dir / "logo_banner.png"
    banner.save(banner_path, format="PNG")
    print(f"[OK] Generated {banner_path}")


if __name__ == "__main__":
    main()
