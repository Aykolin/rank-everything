from dataclasses import dataclass

from rank_everything.models import RankItem


@dataclass(slots=True)
class ComparisonSession:
    items: list[RankItem]
    low: int = 0
    high: int | None = None
    comparisons: int = 0

    def __post_init__(self) -> None:
        self.high = len(self.items) if self.high is None else self.high

    @property
    def finished(self) -> bool:
        return self.low >= self.high

    @property
    def current(self) -> RankItem | None:
        if self.finished:
            return None
        return self.items[(self.low + self.high) // 2]

    @property
    def result_index(self) -> int:
        if not self.finished:
            raise RuntimeError("A comparação ainda não terminou")
        return self.low

    def choose(self, new_item_wins: bool) -> None:
        if self.finished:
            return
        midpoint = (self.low + self.high) // 2
        if new_item_wins:
            self.high = midpoint
        else:
            self.low = midpoint + 1
        self.comparisons += 1


def parse_score(value: str) -> float:
    normalized = value.strip().replace(",", ".")
    score = float(normalized)
    if score < 0 or score > 10:
        raise ValueError("A nota precisa estar entre 0 e 10")
    return round(score, 1)

