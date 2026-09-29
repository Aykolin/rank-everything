from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutProfile:
    width: float
    height: float
    compact: bool
    phone: bool
    tablet: bool
    short: bool
    outer_horizontal: int
    outer_vertical: int
    heading_size: int
    subtitle_size: int
    appbar_height: int
    grid_max_extent: int
    grid_aspect_ratio: float
    card_padding: int
    section_padding: int
    item_badge_size: int
    item_padding: int
    comparison_height: int


def layout_profile(width: float | None, height: float | None) -> LayoutProfile:
    safe_width = max(float(width or 390), 280)
    safe_height = max(float(height or 844), 320)
    compact = safe_width < 380
    phone = safe_width < 600
    tablet = safe_width < 960
    short = safe_height < 600

    if compact:
        outer_horizontal = 12
        heading_size = 27
        card_padding = 16
        section_padding = 16
        item_badge_size = 42
        item_padding = 8
    elif phone:
        outer_horizontal = 16
        heading_size = 31
        card_padding = 18
        section_padding = 20
        item_badge_size = 46
        item_padding = 10
    elif tablet:
        outer_horizontal = 24
        heading_size = 34
        card_padding = 20
        section_padding = 22
        item_badge_size = 48
        item_padding = 10
    else:
        outer_horizontal = 32
        heading_size = 36
        card_padding = 20
        section_padding = 24
        item_badge_size = 48
        item_padding = 10

    if safe_width < 380:
        grid_max_extent = 600
        grid_aspect_ratio = 1.45
    elif safe_width < 680:
        grid_max_extent = 600
        grid_aspect_ratio = 1.72
    elif safe_width < 960:
        grid_max_extent = 360
        grid_aspect_ratio = 1.38
    else:
        grid_max_extent = 340
        grid_aspect_ratio = 1.34

    return LayoutProfile(
        width=safe_width,
        height=safe_height,
        compact=compact,
        phone=phone,
        tablet=tablet,
        short=short,
        outer_horizontal=outer_horizontal,
        outer_vertical=12 if short else (16 if phone else 24),
        heading_size=heading_size,
        subtitle_size=13 if compact else 14,
        appbar_height=56 if short or compact else (60 if phone else 64),
        grid_max_extent=grid_max_extent,
        grid_aspect_ratio=grid_aspect_ratio,
        card_padding=card_padding,
        section_padding=section_padding,
        item_badge_size=item_badge_size,
        item_padding=item_padding,
        comparison_height=138 if short else (154 if phone else 176),
    )
