import flet as ft


ROSEWATER = "#F5E0DC"
FLAMINGO = "#F2CDCD"
PINK = "#F5C2E7"
MAUVE = "#CBA6F7"
RED = "#F38BA8"
MAROON = "#EBA0AC"
PEACH = "#FAB387"
YELLOW = "#F9E2AF"
GREEN = "#A6E3A1"
TEAL = "#94E2D5"
SKY = "#89DCEB"
SAPPHIRE = "#74C7EC"
BLUE = "#89B4FA"
LAVENDER = "#B4BEFE"
TEXT = "#CDD6F4"
SUBTEXT_1 = "#BAC2DE"
SUBTEXT_0 = "#A6ADC8"
OVERLAY_2 = "#9399B2"
OVERLAY_1 = "#7F849C"
OVERLAY_0 = "#6C7086"
SURFACE_2 = "#585B70"
SURFACE_1 = "#45475A"
SURFACE_0 = "#313244"
BASE = "#1E1E2E"
MANTLE = "#181825"
CRUST = "#11111B"

CREAM = BASE
INK = TEXT
OLIVE = GREEN
WHITE = SURFACE_0
MUTED = SUBTEXT_0
ERROR = RED
OUTLINE = SURFACE_1

RANKING_COLORS = {
    "rosewater": ROSEWATER,
    "flamingo": FLAMINGO,
    "pink": PINK,
    "mauve": MAUVE,
    "red": RED,
    "maroon": MAROON,
    "peach": PEACH,
    "yellow": YELLOW,
    "green": GREEN,
    "teal": TEAL,
    "sky": SKY,
    "sapphire": SAPPHIRE,
    "blue": BLUE,
    "lavender": LAVENDER,
    "olive": GREEN,
}

RANKING_COLOR_LABELS = {
    "rosewater": "Rosewater",
    "flamingo": "Flamingo",
    "pink": "Pink",
    "mauve": "Mauve",
    "red": "Red",
    "maroon": "Maroon",
    "peach": "Peach",
    "yellow": "Yellow",
    "green": "Green",
    "teal": "Teal",
    "sky": "Sky",
    "sapphire": "Sapphire",
    "blue": "Blue",
    "lavender": "Lavender",
}

RANKING_ICONS = {
    "star": ft.Icons.STAR_ROUNDED,
    "trophy": ft.Icons.EMOJI_EVENTS_ROUNDED,
    "favorite": ft.Icons.FAVORITE_ROUNDED,
    "restaurant": ft.Icons.RESTAURANT_ROUNDED,
    "coffee": ft.Icons.COFFEE_ROUNDED,
    "cake": ft.Icons.CAKE_ROUNDED,
    "game": ft.Icons.SPORTS_ESPORTS_ROUNDED,
    "movie": ft.Icons.MOVIE_ROUNDED,
    "music": ft.Icons.HEADPHONES_ROUNDED,
    "book": ft.Icons.MENU_BOOK_ROUNDED,
    "place": ft.Icons.TRAVEL_EXPLORE_ROUNDED,
    "flight": ft.Icons.FLIGHT_ROUNDED,
    "camera": ft.Icons.CAMERA_ALT_ROUNDED,
    "palette": ft.Icons.PALETTE_ROUNDED,
    "fitness": ft.Icons.FITNESS_CENTER_ROUNDED,
    "sports": ft.Icons.SPORTS_BASKETBALL_ROUNDED,
    "tech": ft.Icons.DEVICES_ROUNDED,
    "shopping": ft.Icons.SHOPPING_BAG_ROUNDED,
    "nature": ft.Icons.PARK_ROUNDED,
    "pet": ft.Icons.PETS_ROUNDED,
    "idea": ft.Icons.LIGHTBULB_ROUNDED,
    "work": ft.Icons.WORK_ROUNDED,
    "school": ft.Icons.SCHOOL_ROUNDED,
    "spark": ft.Icons.AUTO_AWESOME_ROUNDED,
}

RANKING_ICON_LABELS = {
    "star": "Estrela",
    "trophy": "Troféu",
    "favorite": "Favorito",
    "restaurant": "Comida",
    "coffee": "Café",
    "cake": "Doces",
    "game": "Jogos",
    "movie": "Filmes",
    "music": "Música",
    "book": "Livros",
    "place": "Lugares",
    "flight": "Viagens",
    "camera": "Fotos",
    "palette": "Arte",
    "fitness": "Fitness",
    "sports": "Esportes",
    "tech": "Tecnologia",
    "shopping": "Compras",
    "nature": "Natureza",
    "pet": "Animais",
    "idea": "Ideias",
    "work": "Trabalho",
    "school": "Estudos",
    "spark": "Destaques",
}

RANKING_ICON_COLORS = {
    key: color
    for key, color in zip(
        RANKING_ICONS,
        [
            YELLOW, PEACH, PINK, RED, FLAMINGO, ROSEWATER,
            MAUVE, BLUE, LAVENDER, SAPPHIRE, SKY, TEAL,
            PINK, MAUVE, GREEN, PEACH, BLUE, FLAMINGO,
            GREEN, ROSEWATER, YELLOW, SAPPHIRE, LAVENDER, TEAL,
        ],
    )
}


def build_theme() -> ft.Theme:
    return ft.Theme(
        use_material3=True,
        font_family="Arial",
        scaffold_bgcolor=BASE,
        color_scheme=ft.ColorScheme(
            primary=MAUVE,
            on_primary=CRUST,
            primary_container=SURFACE_1,
            on_primary_container=TEXT,
            secondary=BLUE,
            on_secondary=CRUST,
            secondary_container=SURFACE_0,
            on_secondary_container=TEXT,
            tertiary=TEAL,
            on_tertiary=CRUST,
            surface=BASE,
            on_surface=TEXT,
            surface_container=MANTLE,
            surface_container_high=SURFACE_0,
            outline=SURFACE_1,
            outline_variant=SURFACE_0,
            error=RED,
            on_error=CRUST,
        ),
    )


def field_border(color: str = SURFACE_1, width: float = 1) -> ft.OutlineInputBorder:
    return ft.OutlineInputBorder(
        side=ft.BorderSide(width=width, color=color),
        border_radius=16,
    )


def primary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=MAUVE,
        color=CRUST,
        padding=ft.Padding.symmetric(horizontal=22, vertical=16),
        shape=ft.RoundedRectangleBorder(radius=16),
        elevation=0,
    )


def secondary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=SURFACE_0,
        color=TEXT,
        padding=ft.Padding.symmetric(horizontal=18, vertical=14),
        side=ft.BorderSide(width=1, color=SURFACE_1),
        shape=ft.RoundedRectangleBorder(radius=16),
        elevation=0,
    )


def soft_shadow(color: str = CRUST) -> ft.BoxShadow:
    return ft.BoxShadow(
        blur_radius=24,
        spread_radius=-8,
        color=f"66{color.lstrip('#')}",
        offset=ft.Offset(0, 10),
    )
