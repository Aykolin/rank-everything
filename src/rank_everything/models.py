from dataclasses import dataclass


@dataclass(slots=True)
class Ranking:
    id: int
    name: str
    description: str
    sort_mode: str
    color_key: str
    icon_key: str
    created_at: str
    updated_at: str
    item_count: int = 0
    leader_name: str | None = None


@dataclass(slots=True)
class RankItem:
    id: int
    ranking_id: int
    name: str
    subtitle: str
    score: float | None
    note: str
    image_path: str | None
    position: int
    created_at: str
    updated_at: str

