from rank_everything.layout import layout_profile


def test_compact_phone_uses_dense_single_column_layout():
    profile = layout_profile(320, 568)

    assert profile.compact
    assert profile.phone
    assert profile.outer_horizontal == 12
    assert profile.grid_max_extent == 600
    assert profile.appbar_height == 56
    assert profile.comparison_height == 138


def test_regular_phone_preserves_readable_spacing():
    profile = layout_profile(412, 915)

    assert not profile.compact
    assert profile.phone
    assert profile.outer_horizontal == 16
    assert profile.heading_size == 31
    assert profile.grid_aspect_ratio == 1.72


def test_landscape_phone_uses_short_height_rules():
    profile = layout_profile(844, 390)

    assert not profile.phone
    assert profile.tablet
    assert profile.short
    assert profile.outer_vertical == 12
    assert profile.comparison_height == 138


def test_tablet_and_desktop_expand_content_progressively():
    tablet = layout_profile(800, 1280)
    desktop = layout_profile(1440, 900)

    assert tablet.grid_max_extent == 360
    assert tablet.outer_horizontal == 24
    assert desktop.grid_max_extent == 340
    assert desktop.outer_horizontal == 32
    assert desktop.heading_size > tablet.heading_size


def test_invalid_dimensions_fall_back_to_safe_minimums():
    profile = layout_profile(0, 0)

    assert profile.width >= 280
    assert profile.height >= 320
