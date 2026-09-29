from rank_everything.models import RankItem
from rank_everything.services import ComparisonSession, parse_score


def item(item_id: int, name: str, position: int) -> RankItem:
    return RankItem(
        id=item_id,
        ranking_id=1,
        name=name,
        subtitle="",
        score=None,
        note="",
        image_path=None,
        position=position,
        created_at="",
        updated_at="",
    )


def test_comparison_finds_first_position():
    session = ComparisonSession([item(1, "A", 0), item(2, "B", 1), item(3, "C", 2)])

    while not session.finished:
        session.choose(new_item_wins=True)

    assert session.result_index == 0


def test_comparison_finds_last_position():
    session = ComparisonSession([item(1, "A", 0), item(2, "B", 1), item(3, "C", 2)])

    while not session.finished:
        session.choose(new_item_wins=False)

    assert session.result_index == 3


def test_comparison_finds_middle_position():
    session = ComparisonSession(
        [item(1, "A", 0), item(2, "B", 1), item(3, "C", 2), item(4, "D", 3)]
    )

    session.choose(True)
    session.choose(False)

    assert session.finished
    assert session.result_index == 2


def test_parse_score_accepts_comma_and_validates_range():
    assert parse_score("9,45") == 9.4

    try:
        parse_score("11")
    except ValueError as error:
        assert "entre 0 e 10" in str(error)
    else:
        raise AssertionError("A nota inválida deveria falhar")
