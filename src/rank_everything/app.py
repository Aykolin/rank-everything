import os
from pathlib import Path
from typing import Callable

import flet as ft

from rank_everything.database import Database
from rank_everything.i18n import SUPPORTED_LANGUAGES, translate
from rank_everything.layout import LayoutProfile, layout_profile
from rank_everything.models import RankItem, Ranking
from rank_everything.navigation import route_stack
from rank_everything.repository import CatalogRepository
from rank_everything.services import ComparisonSession, parse_score
from rank_everything.theme import (
    BASE,
    BLUE,
    CREAM,
    CRUST,
    ERROR,
    GREEN,
    INK,
    MANTLE,
    MAUVE,
    MUTED,
    OLIVE,
    OUTLINE,
    PEACH,
    PINK,
    RANKING_COLOR_LABELS,
    RANKING_COLORS,
    RANKING_ICON_COLORS,
    RANKING_ICONS,
    SUBTEXT_1,
    SURFACE_0,
    SURFACE_1,
    SURFACE_2,
    TEAL,
    TEXT,
    WHITE,
    YELLOW,
    build_theme,
    field_border,
    primary_button_style,
    secondary_button_style,
    soft_shadow,
)


APP_VERSION = "0.5.0"


class RankEverythingApp:
    def __init__(self, page: ft.Page, repository: CatalogRepository):
        self.page = page
        self.repository = repository
        saved_language = self.repository.get_preference("language", "pt-BR")
        self.language = (
            saved_language if saved_language in SUPPORTED_LANGUAGES else "pt-BR"
        )
        self.current_ranking_id: int | None = None
        self.search_query = ""
        self.pending_item: dict[str, str | float | None] | None = None
        self.comparison: ComparisonSession | None = None
        self._building_route = "/"
        self.layout = layout_profile(self.page.width, self.page.height)
        self._responsive_bindings: list[
            tuple[ft.Control, Callable[[ft.Control, LayoutProfile], None]]
        ] = []

        self.page.title = "Rank Everything"
        self.page.theme = build_theme()
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BASE
        self.page.padding = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.on_resize = self._handle_resize
        self.page.on_route_change = self._handle_route_change
        self.page.on_view_pop = self._handle_view_pop

    def _handle_resize(self, event: ft.PageResizeEvent) -> None:
        self.layout = layout_profile(event.width, event.height)
        for control, apply in self._responsive_bindings:
            apply(control, self.layout)
        self.page.update()

    def _responsive(
        self,
        control: ft.Control,
        apply: Callable[[ft.Control, LayoutProfile], None],
    ) -> ft.Control:
        apply(control, self.layout)
        self._responsive_bindings.append((control, apply))
        return control

    def start(self) -> None:
        self._handle_route_change()

    def _t(self, key: str, **values) -> str:
        return translate(self.language, key, **values)

    def _change_language(self, event) -> None:
        language = event.control.value
        if language not in SUPPORTED_LANGUAGES or language == self.language:
            return
        self.language = language
        self.repository.set_preference("language", language)
        self._handle_route_change()

    def _handle_route_change(self, _=None) -> None:
        self.page.views.clear()
        targets = route_stack(self.page.route)

        for target in targets:
            if target.ranking_id is not None and self.repository.get_ranking(target.ranking_id) is None:
                break

            self._building_route = target.route
            if target.screen == "home":
                self.render_home()
            elif target.screen == "settings":
                self.render_settings()
            elif target.screen == "create_ranking":
                self.render_create_ranking()
            elif target.screen == "ranking":
                self.render_ranking(target.ranking_id)
            elif target.screen == "add_item":
                self.render_add_item(target.ranking_id)
            elif target.screen == "comparison":
                if self.pending_item is None or self.comparison is None:
                    self.page.navigate(f"/rankings/{target.ranking_id}/add")
                    break
                self.render_comparison(target.ranking_id)

        self.page.update()

    async def _handle_view_pop(self, event: ft.ViewPopEvent) -> None:
        if len(self.page.views) <= 1 or event.view is None:
            return
        if event.view in self.page.views:
            self.page.views.remove(event.view)
        await self.page.push_route(self.page.views[-1].route)

    def render_home(self) -> None:
        self.current_ranking_id = None
        rankings = self.repository.list_rankings(self.search_query)
        self._base_page(0)
        self._view_floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=MAUVE,
            foreground_color=CRUST,
            tooltip=self._t("home.create_tooltip"),
            on_click=lambda _: self.page.navigate("/rankings/new"),
        )

        search = ft.TextField(
            value=self.search_query,
            hint_text=self._t("home.search"),
            prefix_icon=ft.Icons.SEARCH,
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            bgcolor=MANTLE,
            color=TEXT,
            cursor_color=MAUVE,
            col={"xs": 12, "sm": 9, "md": 7, "lg": 5},
            on_submit=self._search,
            on_change=lambda e: setattr(self, "search_query", e.control.value),
        )

        if rankings:
            cards = ft.GridView(
                controls=[self._ranking_card(ranking) for ranking in rankings],
                max_extent=self.layout.grid_max_extent,
                child_aspect_ratio=self.layout.grid_aspect_ratio,
                spacing=16,
                run_spacing=16,
                expand=True,
            )
            self._responsive(
                cards,
                lambda control, profile: (
                    setattr(control, "max_extent", profile.grid_max_extent),
                    setattr(control, "child_aspect_ratio", profile.grid_aspect_ratio),
                    setattr(control, "spacing", 12 if profile.compact else 16),
                    setattr(control, "run_spacing", 12 if profile.compact else 16),
                ),
            )
        else:
            cards = self._empty_home()

        content = ft.Column(
            controls=[
                self._page_heading(
                    self._t("home.title"),
                    self._t(
                        "home.collection_one" if len(rankings) == 1 else "home.collection_many",
                        count=len(rankings),
                    ),
                ),
                ft.ResponsiveRow(controls=[search], spacing=0, run_spacing=0),
                cards,
            ],
            spacing=20,
            expand=True,
        )
        self._show(content)

    def render_create_ranking(self) -> None:
        self._base_page(None)
        self._view_appbar = self._appbar(self._t("ranking.new_appbar"), "/")

        name = self._field(
            self._t("ranking.name"),
            self._t("ranking.name_hint"),
            60,
        )
        description = self._field(
            self._t("ranking.description"),
            self._t("ranking.description_hint"),
            240,
            multiline=True,
        )
        mode = ft.Dropdown(
            value="position",
            label=self._t("ranking.sort_label"),
            width=float("inf"),
            options=[
                ft.DropdownOption(key="position", text=self._t("ranking.sort_position")),
                ft.DropdownOption(key="score", text=self._t("ranking.sort_score")),
            ],
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
        )
        color = ft.Dropdown(
            value="mauve",
            label=self._t("ranking.cover_color"),
            width=float("inf"),
            options=[
                ft.DropdownOption(
                    key=key,
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=18,
                                height=18,
                                bgcolor=RANKING_COLORS[key],
                                border_radius=6,
                            ),
                            ft.Text(label),
                        ],
                        spacing=10,
                        tight=True,
                    ),
                )
                for key, label in RANKING_COLOR_LABELS.items()
            ],
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
        )
        icon = ft.Dropdown(
            value="star",
            label=self._t("ranking.symbol"),
            width=float("inf"),
            options=[
                ft.DropdownOption(
                    key=key,
                    content=ft.Row(
                        controls=[
                            ft.Icon(symbol, color=RANKING_ICON_COLORS[key], size=20),
                            ft.Text(self._t(f"icon.{key}")),
                        ],
                        spacing=10,
                        tight=True,
                    ),
                )
                for key, symbol in RANKING_ICONS.items()
            ],
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
        )

        def save(_):
            clean_name = name.value.strip()
            if not clean_name:
                name.error = self._t("ranking.name_error")
                name.update()
                return
            ranking_id = self.repository.create_ranking(
                clean_name,
                description.value,
                mode.value,
                color.value,
                icon.value,
            )
            self.current_ranking_id = ranking_id
            self.page.navigate(f"/rankings/{ranking_id}")

        content = self._form_layout(
            [
                self._page_heading(
                    self._t("ranking.create_title"),
                    self._t("ranking.create_subtitle"),
                ),
                name,
                description,
                mode,
                color,
                icon,
                ft.Container(height=4),
                ft.Button(
                    self._t("ranking.create_button"),
                    icon=ft.Icons.ADD,
                    style=primary_button_style(),
                    on_click=save,
                ),
            ]
        )
        self._show(content)

    def render_ranking(self, ranking_id: int) -> None:
        ranking = self.repository.get_ranking(ranking_id)
        if ranking is None:
            self.page.navigate("/")
            return

        self.current_ranking_id = ranking_id
        items = self.repository.list_items(ranking_id)
        self._base_page(None)
        self._view_appbar = self._appbar(
            ranking.name,
            "/",
            [
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_HORIZ,
                    items=[
                        ft.PopupMenuItem(
                            content=self._t("ranking.delete_menu"),
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=lambda _: self._confirm_delete_ranking(ranking),
                        )
                    ],
                )
            ],
        )
        self._view_floating_action_button = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=MAUVE,
            foreground_color=CRUST,
            tooltip=self._t("ranking.add_tooltip"),
            on_click=lambda _: self.page.navigate(f"/rankings/{ranking_id}/add"),
        )

        header = self._ranking_header(ranking, items)
        if not items:
            body = self._empty_ranking(ranking_id)
        elif ranking.sort_mode == "position":
            body = ft.ReorderableListView(
                controls=[
                    self._item_row(ranking, item, index, len(items))
                    for index, item in enumerate(items)
                ],
                show_default_drag_handles=False,
                spacing=10,
                on_reorder=lambda e: self._reorder_items(ranking_id, e),
                expand=True,
            )
        else:
            body = ft.ListView(
                controls=[
                    self._item_row(ranking, item, index, len(items))
                    for index, item in enumerate(items)
                ],
                spacing=10,
                expand=True,
            )

        content = ft.Column(controls=[header, body], spacing=18, expand=True)
        self._show(content)

    def render_add_item(self, ranking_id: int) -> None:
        ranking = self.repository.get_ranking(ranking_id)
        if ranking is None:
            self.page.navigate("/")
            return
        items = self.repository.list_items(ranking_id)
        self._base_page(None)
        self._view_appbar = self._appbar(
            self._t("item.add_appbar"),
            f"/rankings/{ranking_id}",
        )

        name = self._field(self._t("item.name"), self._t("item.name_hint"), 80)
        subtitle = self._field(
            self._t("item.subtitle"),
            self._t("item.subtitle_hint"),
            80,
        )
        note = self._field(
            self._t("item.note"),
            self._t("item.note_hint"),
            1000,
            multiline=True,
        )
        score = self._field(
            self._t("item.score"),
            self._t("item.score_hint"),
            4,
        )
        add_mode = ft.Dropdown(
            value="compare" if items else "end",
            label=self._t("item.place_label"),
            width=float("inf"),
            options=[
                ft.DropdownOption(key="compare", text=self._t("item.place_compare")),
                ft.DropdownOption(key="end", text=self._t("item.place_end")),
            ],
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
            visible=ranking.sort_mode == "position" and bool(items),
        )

        def save(_):
            clean_name = name.value.strip()
            if not clean_name:
                name.error = self._t("item.name_error")
                name.update()
                return

            parsed_score = None
            if ranking.sort_mode == "score":
                try:
                    parsed_score = parse_score(score.value)
                except (ValueError, TypeError):
                    score.error = self._t("item.score_error")
                    score.update()
                    return

            data = {
                "name": clean_name,
                "subtitle": subtitle.value,
                "note": note.value,
                "score": parsed_score,
            }
            if ranking.sort_mode == "position" and items and add_mode.value == "compare":
                self.pending_item = data
                self.comparison = ComparisonSession(items)
                self.page.navigate(f"/rankings/{ranking_id}/compare")
                return

            self.repository.create_item(ranking_id, **data)
            self._notice(self._t("item.added"))
            self.page.navigate(f"/rankings/{ranking_id}")

        controls = [
            self._page_heading(
                self._t("item.new_title"),
                self._t("item.new_subtitle", ranking=ranking.name),
            ),
            name,
            subtitle,
        ]
        if ranking.sort_mode == "score":
            controls.append(score)
        controls.extend(
            [
                note,
                add_mode,
                ft.Button(
                    self._t("item.save"),
                    icon=ft.Icons.CHECK,
                    style=primary_button_style(),
                    on_click=save,
                ),
            ]
        )
        self._show(self._form_layout(controls))

    def render_comparison(self, ranking_id: int) -> None:
        if self.pending_item is None or self.comparison is None:
            self.page.navigate(f"/rankings/{ranking_id}/add")
            return
        if self.comparison.finished:
            self.repository.create_item(
                ranking_id,
                **self.pending_item,
                position=self.comparison.result_index,
            )
            self.pending_item = None
            self.comparison = None
            self._notice(self._t("item.position_set"))
            self.page.navigate(f"/rankings/{ranking_id}")
            return

        candidate = self.comparison.current
        if candidate is None:
            self.page.navigate(f"/rankings/{ranking_id}")
            return

        self._base_page(None)
        self._view_appbar = self._appbar(
            self._t("comparison.appbar"),
            f"/rankings/{ranking_id}/add",
        )
        new_name = str(self.pending_item["name"])
        progress = self.comparison.comparisons + 1

        def choose(new_wins: bool):
            self.comparison.choose(new_wins)
            self._handle_route_change()

        choices = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    content=self._comparison_card(new_name, PINK, lambda _: choose(True)),
                    col={"xs": 12, "md": 6},
                ),
                ft.Container(
                    content=self._comparison_card(candidate.name, BLUE, lambda _: choose(False)),
                    col={"xs": 12, "md": 6},
                ),
            ],
            spacing={"xs": 0, "md": 14},
            run_spacing=12,
        )
        content = ft.Column(
            controls=[
                self._page_heading(
                    self._t("comparison.title"),
                    self._t("comparison.subtitle", number=progress),
                ),
                ft.Container(
                    content=ft.Text(
                        self._t("comparison.instruction"),
                        size=11,
                        weight=ft.FontWeight.W_600,
                        color=MUTED,
                    ),
                    alignment=ft.Alignment.CENTER_LEFT,
                ),
                choices,
                ft.TextButton(
                    self._t("comparison.skip"),
                    on_click=lambda _: self._finish_at_end(ranking_id),
                ),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self._show(content)

    def render_settings(self) -> None:
        self._base_page(1)
        language = ft.Dropdown(
            value=self.language,
            label=self._t("settings.language"),
            helper_text=self._t("settings.language_help"),
            width=float("inf"),
            options=[
                ft.DropdownOption(key=key, text=label)
                for key, label in SUPPORTED_LANGUAGES.items()
            ],
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
            on_select=self._change_language,
        )
        tiles = ft.ResponsiveRow(
            controls=[
                self._settings_tile(
                    ft.Icons.CLOUD_OFF_OUTLINED,
                    self._t("settings.offline_title"),
                    self._t("settings.offline_text"),
                    BLUE,
                ),
                self._settings_tile(
                    ft.Icons.STORAGE_OUTLINED,
                    self._t("settings.database_title"),
                    self._t("settings.database_text"),
                    OLIVE,
                ),
                self._settings_tile(
                    ft.Icons.INFO_OUTLINE,
                    self._t("settings.version_title", version=APP_VERSION),
                    self._t("settings.version_text"),
                    PINK,
                ),
            ],
            spacing=14,
            run_spacing=14,
        )
        content = ft.Column(
            controls=[
                self._page_heading(
                    self._t("settings.title"),
                    self._t("settings.subtitle"),
                ),
                language,
                tiles,
            ],
            spacing=14,
            expand=True,
        )
        self._show(content)

    def _base_page(self, navigation_index: int | None) -> None:
        self._responsive_bindings.clear()
        self.layout = layout_profile(self.page.width, self.page.height)
        self._view_appbar = None
        self._view_floating_action_button = None
        self._view_navigation_bar = None
        if navigation_index is None:
            return
        self._view_navigation_bar = ft.NavigationBar(
            selected_index=navigation_index,
            bgcolor=MANTLE,
            indicator_color=MAUVE,
            elevation=0,
            animation_duration=260,
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
            border=ft.Border.only(top=ft.BorderSide(1, SURFACE_0)),
            on_change=self._change_navigation,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.GRID_VIEW_OUTLINED,
                    selected_icon=ft.Icons.GRID_VIEW,
                    label=self._t("nav.rankings"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.TUNE_OUTLINED,
                    selected_icon=ft.Icons.TUNE,
                    label=self._t("nav.settings"),
                ),
            ],
        )

    def _show(self, content: ft.Control) -> None:
        inner = ft.Container(
            content=content,
            width=1180,
            expand=True,
        )
        outer = ft.Container(
            content=inner,
            padding=ft.Padding.symmetric(
                horizontal=self.layout.outer_horizontal,
                vertical=self.layout.outer_vertical,
            ),
            alignment=ft.Alignment.TOP_CENTER,
            expand=True,
        )
        self._responsive(
            outer,
            lambda control, profile: setattr(
                control,
                "padding",
                ft.Padding.symmetric(
                    horizontal=profile.outer_horizontal,
                    vertical=profile.outer_vertical,
                ),
            ),
        )
        self.page.views.append(
            ft.View(
                route=self._building_route,
                controls=[ft.SafeArea(content=outer, expand=True)],
                appbar=self._view_appbar,
                navigation_bar=self._view_navigation_bar,
                floating_action_button=self._view_floating_action_button,
                bgcolor=BASE,
                padding=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=0,
            )
        )

    def _form_layout(self, controls: list[ft.Control]) -> ft.Control:
        return ft.Column(
            controls=controls,
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _appbar(self, title: str, back_route: str, actions=None) -> ft.AppBar:
        async def go_back(_):
            await self.page.pop_views_until(back_route)

        title_control = ft.Text(
            title,
            size=18 if self.layout.compact else 20,
            weight=ft.FontWeight.W_600,
            color=TEXT,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=TEXT,
                tooltip=self._t("common.back"),
                on_click=go_back,
            ),
            title=title_control,
            actions=actions or [],
            color=TEXT,
            bgcolor=MANTLE,
            elevation=0,
            elevation_on_scroll=0,
            toolbar_height=self.layout.appbar_height,
        )
        self._responsive(
            appbar,
            lambda control, profile: setattr(
                control, "toolbar_height", profile.appbar_height
            ),
        )
        self._responsive(
            title_control,
            lambda control, profile: setattr(
                control, "size", 18 if profile.compact else 20
            ),
        )
        return appbar

    def _page_heading(self, title: str, subtitle: str) -> ft.Control:
        title_control = ft.Text(
            title,
            size=self.layout.heading_size,
            weight=ft.FontWeight.BOLD,
            color=TEXT,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        subtitle_control = ft.Text(
            subtitle,
            size=self.layout.subtitle_size,
            color=SUBTEXT_1,
        )
        self._responsive(
            title_control,
            lambda control, profile: setattr(control, "size", profile.heading_size),
        )
        self._responsive(
            subtitle_control,
            lambda control, profile: setattr(control, "size", profile.subtitle_size),
        )
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=7,
                            height=7,
                            bgcolor=MAUVE,
                            border_radius=99,
                        ),
                        ft.Text(
                            self._t("common.your_space"),
                            size=11,
                            weight=ft.FontWeight.W_600,
                            color=MAUVE,
                        ),
                    ],
                    spacing=8,
                ),
                title_control,
                subtitle_control,
            ],
            spacing=5,
        )

    def _ranking_card(self, ranking: Ranking) -> ft.Control:
        color = RANKING_COLORS.get(ranking.color_key, PINK)
        icon = RANKING_ICONS.get(ranking.icon_key, ft.Icons.STAR_ROUNDED)
        icon_color = RANKING_ICON_COLORS.get(ranking.icon_key, YELLOW)
        leader = ranking.leader_name or self._t("home.no_champion")
        icon_box = ft.Container(
            content=ft.Icon(icon, size=24, color=icon_color),
            width=44,
            height=44,
            bgcolor=SURFACE_1,
            border_radius=14,
            alignment=ft.Alignment.CENTER,
        )
        arrow_box = ft.Container(
            content=ft.Icon(ft.Icons.ARROW_OUTWARD, size=18, color=SUBTEXT_1),
            width=36,
            height=36,
            bgcolor=SURFACE_1,
            border_radius=12,
            alignment=ft.Alignment.CENTER,
        )
        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            icon_box,
                            ft.Container(expand=True),
                            arrow_box,
                        ]
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        ranking.name,
                        size=21,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Row(
                        controls=[
                            ft.Container(width=18, height=5, bgcolor=color, border_radius=99),
                            ft.Text(
                                self._t(
                                    "home.item_one" if ranking.item_count == 1 else "home.item_many",
                                    count=ranking.item_count,
                                ),
                                size=12,
                                color=SUBTEXT_1,
                            ),
                            ft.Container(width=4, height=4, bgcolor=SURFACE_2, border_radius=99),
                            ft.Text(
                                f"#1 {leader}",
                                size=12,
                                color=color,
                                weight=ft.FontWeight.W_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=9,
                expand=True,
            ),
            bgcolor=SURFACE_0,
            border=ft.Border.all(1, SURFACE_1),
            border_radius=18 if self.layout.compact else 22,
            padding=self.layout.card_padding,
            shadow=soft_shadow(),
            ink=True,
            ink_color=SURFACE_1,
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT_CUBIC),
            on_hover=self._lift_on_hover,
            on_click=lambda _: self.page.navigate(f"/rankings/{ranking.id}"),
        )
        self._responsive(
            card,
            lambda control, profile: (
                setattr(control, "padding", profile.card_padding),
                setattr(control, "border_radius", 18 if profile.compact else 22),
            ),
        )
        self._responsive(
            icon_box,
            lambda control, profile: (
                setattr(control, "width", 40 if profile.compact else 44),
                setattr(control, "height", 40 if profile.compact else 44),
            ),
        )
        self._responsive(
            arrow_box,
            lambda control, profile: (
                setattr(control, "width", 34 if profile.compact else 36),
                setattr(control, "height", 34 if profile.compact else 36),
            ),
        )
        return card

    def _ranking_header(self, ranking: Ranking, items: list[RankItem]) -> ft.Control:
        color = RANKING_COLORS.get(ranking.color_key, PINK)
        icon = RANKING_ICONS.get(ranking.icon_key, ft.Icons.STAR_ROUNDED)
        icon_color = RANKING_ICON_COLORS.get(ranking.icon_key, YELLOW)
        mode = self._t(
            "ranking.mode_manual" if ranking.sort_mode == "position" else "ranking.mode_score"
        )
        leader = items[0].name if items else self._t("ranking.no_items")
        icon_box = ft.Container(
            content=ft.Icon(icon, size=30, color=icon_color),
            width=58,
            height=58,
            bgcolor=SURFACE_1,
            border_radius=18,
            alignment=ft.Alignment.CENTER,
        )
        count_text = ft.Text(
            f"{len(items):02d}",
            size=42,
            color=TEXT,
            weight=ft.FontWeight.BOLD,
        )
        leader_text = ft.Text(
            leader,
            size=20,
            color=TEXT,
            weight=ft.FontWeight.BOLD,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        header = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                icon_box,
                                ft.Text(mode.upper(), size=10, color=color, weight=ft.FontWeight.W_600),
                            ],
                            spacing=14,
                        ),
                        col={"xs": 12, "sm": 4, "md": 3},
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    self._t("ranking.ranked_items"),
                                    size=11,
                                    color=SUBTEXT_1,
                                    weight=ft.FontWeight.W_600,
                                ),
                                count_text,
                            ],
                            spacing=4,
                        ),
                        col={"xs": 6, "sm": 4, "md": 3},
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    self._t("ranking.current_leader"),
                                    size=11,
                                    color=SUBTEXT_1,
                                    weight=ft.FontWeight.W_600,
                                ),
                                leader_text,
                            ],
                            spacing=6,
                        ),
                        col={"xs": 6, "sm": 4, "md": 6},
                    ),
                ],
                spacing=16,
                run_spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=MANTLE,
            border=ft.Border.all(1, SURFACE_0),
            border_radius=24,
            padding=self.layout.section_padding,
            shadow=soft_shadow(),
        )
        self._responsive(
            header,
            lambda control, profile: setattr(
                control, "padding", profile.section_padding
            ),
        )
        self._responsive(
            icon_box,
            lambda control, profile: (
                setattr(control, "width", 52 if profile.compact else 58),
                setattr(control, "height", 52 if profile.compact else 58),
            ),
        )
        self._responsive(
            count_text,
            lambda control, profile: setattr(control, "size", 36 if profile.compact else 42),
        )
        self._responsive(
            leader_text,
            lambda control, profile: setattr(control, "size", 17 if profile.compact else 20),
        )
        return header

    def _item_row(
        self,
        ranking: Ranking,
        item: RankItem,
        index: int,
        total: int,
    ) -> ft.Control:
        position = index + 1
        position_color = [YELLOW, SUBTEXT_1, PEACH][position - 1] if position <= 3 else SURFACE_2
        trailing_controls = []
        drag_box = None
        if ranking.sort_mode == "score":
            trailing_controls.append(
                ft.Container(
                    content=ft.Text(
                        f"{item.score:.1f}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=CRUST,
                    ),
                    bgcolor=position_color,
                    border_radius=999,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=7),
                )
            )
        else:
            drag_box = ft.Container(
                content=ft.Icon(ft.Icons.DRAG_INDICATOR, color=SUBTEXT_1),
                width=48,
                height=48,
                alignment=ft.Alignment.CENTER,
            )
            trailing_controls.append(
                ft.ReorderableDragHandle(
                    key=f"drag-{item.id}",
                    content=drag_box,
                    mouse_cursor=ft.MouseCursor.GRAB,
                )
            )
        trailing_controls.append(
            ft.PopupMenuButton(
                icon=ft.Icons.MORE_VERT,
                items=[
                    ft.PopupMenuItem(
                        content=self._t("item.move_up"),
                        icon=ft.Icons.ARROW_UPWARD,
                        disabled=index == 0 or ranking.sort_mode == "score",
                        on_click=lambda _, item_index=index: self._move_accessibly(
                            ranking.id, item_index, item_index - 1
                        ),
                    ),
                    ft.PopupMenuItem(
                        content=self._t("item.move_down"),
                        icon=ft.Icons.ARROW_DOWNWARD,
                        disabled=index == total - 1 or ranking.sort_mode == "score",
                        on_click=lambda _, item_index=index: self._move_accessibly(
                            ranking.id, item_index, item_index + 1
                        ),
                    ),
                    ft.PopupMenuItem(
                        content=self._t("common.delete"),
                        icon=ft.Icons.DELETE_OUTLINE,
                        on_click=lambda _, selected=item: self._confirm_delete_item(selected),
                    ),
                ],
            )
        )

        position_box = ft.Container(
            content=ft.Text(
                f"{position:02d}",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=CRUST if position <= 3 else TEXT,
            ),
            width=self.layout.item_badge_size,
            height=self.layout.item_badge_size,
            bgcolor=position_color if position <= 3 else SURFACE_1,
            border_radius=15,
            alignment=ft.Alignment.CENTER,
        )
        name_text = ft.Text(
            item.name,
            size=15 if self.layout.compact else 17,
            weight=ft.FontWeight.BOLD,
            color=TEXT,
            max_lines=2 if self.layout.compact else 1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        subtitle_text = ft.Text(
            item.subtitle or item.note or self._t("item.no_comment"),
            size=12 if self.layout.compact else 13,
            color=SUBTEXT_1,
            max_lines=2 if self.layout.compact else 1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        row = ft.Row(
            controls=[
                position_box,
                ft.Column(
                    controls=[name_text, subtitle_text],
                    spacing=2,
                    expand=True,
                ),
                *trailing_controls,
            ],
            spacing=4 if self.layout.compact else 8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        item_container = ft.Container(
            key=f"item-{item.id}",
            content=row,
            bgcolor=SURFACE_0,
            border=ft.Border.all(1, SURFACE_1),
            border_radius=15 if self.layout.compact else 18,
            padding=ft.Padding.only(
                left=self.layout.item_padding,
                top=self.layout.item_padding,
                right=4 if self.layout.compact else 6,
                bottom=self.layout.item_padding,
            ),
            animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT_CUBIC),
            on_hover=self._lift_on_hover,
        )
        self._responsive(
            position_box,
            lambda control, profile: (
                setattr(control, "width", profile.item_badge_size),
                setattr(control, "height", profile.item_badge_size),
            ),
        )
        self._responsive(
            row,
            lambda control, profile: setattr(control, "spacing", 4 if profile.compact else 8),
        )
        self._responsive(
            name_text,
            lambda control, profile: (
                setattr(control, "size", 15 if profile.compact else 17),
                setattr(control, "max_lines", 2 if profile.compact else 1),
            ),
        )
        self._responsive(
            subtitle_text,
            lambda control, profile: (
                setattr(control, "size", 12 if profile.compact else 13),
                setattr(control, "max_lines", 2 if profile.compact else 1),
            ),
        )
        self._responsive(
            item_container,
            lambda control, profile: (
                setattr(control, "border_radius", 15 if profile.compact else 18),
                setattr(
                    control,
                    "padding",
                    ft.Padding.only(
                        left=profile.item_padding,
                        top=profile.item_padding,
                        right=4 if profile.compact else 6,
                        bottom=profile.item_padding,
                    ),
                ),
            ),
        )
        if drag_box is not None:
            self._responsive(
                drag_box,
                lambda control, profile: (
                    setattr(control, "width", 40 if profile.compact else 48),
                    setattr(control, "height", 40 if profile.compact else 48),
                ),
            )
        return item_container

    def _comparison_card(self, name: str, color: str, on_click) -> ft.Control:
        name_text = ft.Text(
            name,
            size=22 if self.layout.compact else 26,
            color=TEXT,
            weight=ft.FontWeight.BOLD,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=8, height=8, bgcolor=color, border_radius=99),
                            ft.Text(
                                self._t("comparison.choose"),
                                size=11,
                                color=color,
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(expand=True),
                    name_text,
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=24, color=color),
                ],
                spacing=8,
                expand=True,
            ),
            bgcolor=SURFACE_0,
            border=ft.Border.all(1, color),
            border_radius=22,
            padding=self.layout.card_padding,
            height=self.layout.comparison_height,
            ink=True,
            ink_color=SURFACE_1,
            shadow=soft_shadow(),
            animate_scale=ft.Animation(180, ft.AnimationCurve.EASE_OUT_CUBIC),
            on_hover=self._lift_on_hover,
            on_click=on_click,
        )
        self._responsive(
            card,
            lambda control, profile: (
                setattr(control, "padding", profile.card_padding),
                setattr(control, "height", profile.comparison_height),
            ),
        )
        self._responsive(
            name_text,
            lambda control, profile: setattr(control, "size", 22 if profile.compact else 26),
        )
        return card

    def _settings_tile(self, icon, title: str, text: str, color: str) -> ft.Control:
        icon_box = ft.Container(
            content=ft.Icon(icon, color=color),
            bgcolor=SURFACE_1,
            border_radius=16,
            width=52,
            height=52,
            alignment=ft.Alignment.CENTER,
        )
        tile = ft.Container(
            content=ft.Row(
                controls=[
                    icon_box,
                    ft.Column(
                        controls=[
                            ft.Text(title, size=17, color=TEXT, weight=ft.FontWeight.BOLD),
                            ft.Text(text, size=13, color=SUBTEXT_1),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                ],
                spacing=14,
            ),
            bgcolor=SURFACE_0,
            border=ft.Border.all(1, SURFACE_1),
            border_radius=18,
            padding=16,
            animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT_CUBIC),
            on_hover=self._lift_on_hover,
            col={"xs": 12, "md": 6, "lg": 4},
        )
        self._responsive(
            tile,
            lambda control, profile: setattr(control, "padding", 12 if profile.compact else 16),
        )
        self._responsive(
            icon_box,
            lambda control, profile: (
                setattr(control, "width", 44 if profile.compact else 52),
                setattr(control, "height", 44 if profile.compact else 52),
            ),
        )
        return tile

    def _empty_home(self) -> ft.Control:
        empty = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.AUTO_AWESOME, size=34, color=CRUST),
                        width=72,
                        height=72,
                        bgcolor=MAUVE,
                        border_radius=24,
                        alignment=ft.Alignment.CENTER,
                        rotate=0.04,
                    ),
                    ft.Text(
                        self._t("home.empty_title"),
                        size=24,
                        color=TEXT,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        self._t("home.empty_text"),
                        size=14,
                        color=SUBTEXT_1,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        self._t("home.empty_button"),
                        icon=ft.Icons.ADD,
                        style=primary_button_style(),
                        on_click=lambda _: self.page.navigate("/rankings/new"),
                    ),
                ],
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=SURFACE_0,
            border=ft.Border.all(1, SURFACE_1),
            border_radius=24,
            padding=20 if self.layout.compact else 32,
            expand=True,
            alignment=ft.Alignment.CENTER,
            shadow=soft_shadow(),
        )
        self._responsive(
            empty,
            lambda control, profile: setattr(control, "padding", 20 if profile.compact else 32),
        )
        return empty

    def _empty_ranking(self, ranking_id: int) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.FORMAT_LIST_NUMBERED, size=32, color=BLUE),
                        width=64,
                        height=64,
                        bgcolor=SURFACE_0,
                        border_radius=20,
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Text(
                        self._t("ranking.empty_title"),
                        size=22,
                        color=TEXT,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        self._t("ranking.empty_text"),
                        color=SUBTEXT_1,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Button(
                        self._t("ranking.empty_button"),
                        icon=ft.Icons.ADD,
                        style=primary_button_style(),
                        on_click=lambda _: self.page.navigate(f"/rankings/{ranking_id}/add"),
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.Alignment.CENTER,
        )

    def _field(
        self,
        label: str,
        hint: str,
        max_length: int,
        multiline: bool = False,
    ) -> ft.TextField:
        return ft.TextField(
            label=label,
            hint_text=hint,
            width=float("inf"),
            max_length=max_length,
            multiline=multiline,
            min_lines=3 if multiline else None,
            max_lines=5 if multiline else 1,
            border={
                ft.ControlState.DEFAULT: field_border(),
                ft.ControlState.FOCUSED: field_border(MAUVE, 1.5),
            },
            fill_color=MANTLE,
            filled=True,
            color=TEXT,
            cursor_color=MAUVE,
        )

    def _lift_on_hover(self, event) -> None:
        event.control.scale = 1.012 if str(event.data).lower() == "true" else 1
        event.control.update()

    def _change_navigation(self, event) -> None:
        if event.control.selected_index == 0:
            self.page.navigate("/")
        else:
            self.page.navigate("/settings")

    def _search(self, _) -> None:
        self._handle_route_change()

    def _reorder_items(self, ranking_id: int, event) -> None:
        self.repository.move_item(ranking_id, event.old_index, event.new_index)
        self._handle_route_change()

    def _move_accessibly(self, ranking_id: int, old_index: int, new_index: int) -> None:
        self.repository.move_item(ranking_id, old_index, new_index)
        self._handle_route_change()

    def _finish_at_end(self, ranking_id: int) -> None:
        if self.pending_item is not None:
            self.repository.create_item(ranking_id, **self.pending_item)
        self.pending_item = None
        self.comparison = None
        self.page.navigate(f"/rankings/{ranking_id}")

    def _confirm_delete_ranking(self, ranking: Ranking) -> None:
        def confirm(_):
            self.page.pop_dialog()
            self.repository.delete_ranking(ranking.id)
            self.page.navigate("/")

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self._t("dialog.delete_ranking_title"),
                content=ft.Text(
                    self._t("dialog.delete_ranking_text", name=ranking.name)
                ),
                actions=[
                    ft.TextButton(
                        self._t("common.cancel"),
                        on_click=lambda _: self.page.pop_dialog(),
                    ),
                    ft.Button(
                        self._t("common.delete"),
                        bgcolor=ERROR,
                        color=CRUST,
                        on_click=confirm,
                    ),
                ],
            )
        )

    def _confirm_delete_item(self, item: RankItem) -> None:
        def confirm(_):
            self.page.pop_dialog()
            self.repository.delete_item(item.id)
            self._handle_route_change()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=self._t("dialog.delete_item_title"),
                content=ft.Text(self._t("dialog.delete_item_text", name=item.name)),
                actions=[
                    ft.TextButton(
                        self._t("common.cancel"),
                        on_click=lambda _: self.page.pop_dialog(),
                    ),
                    ft.Button(
                        self._t("common.delete"),
                        bgcolor=ERROR,
                        color=CRUST,
                        on_click=confirm,
                    ),
                ],
            )
        )

    def _notice(self, message: str) -> None:
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color=TEXT),
                bgcolor=SURFACE_2,
                show_close_icon=True,
            )
        )


def resolve_database_path() -> Path:
    storage = os.getenv("FLET_APP_STORAGE_DATA")
    if storage:
        return Path(storage) / "rank_everything.db"
    return Path(__file__).resolve().parents[2] / "data" / "rank_everything.db"


def main(page: ft.Page) -> None:
    database = Database(resolve_database_path())
    repository = CatalogRepository(database)
    RankEverythingApp(page, repository).start()

