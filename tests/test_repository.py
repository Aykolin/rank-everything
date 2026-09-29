from pathlib import Path
import sqlite3

from rank_everything.database import Database
from rank_everything.repository import CatalogRepository


def make_repository(tmp_path: Path) -> CatalogRepository:
    return CatalogRepository(Database(tmp_path / "test.db"))


def test_create_and_search_rankings(tmp_path):
    repository = make_repository(tmp_path)
    first = repository.create_ranking(
        "Salames", "Marcas favoritas", "position", "pink", "food"
    )
    repository.create_ranking(
        "Jogos de terror", "Os melhores", "score", "blue", "game"
    )

    results = repository.list_rankings("sala")

    assert [ranking.id for ranking in results] == [first]
    assert results[0].name == "Salames"
    assert results[0].item_count == 0


def test_items_are_reordered_and_renumbered(tmp_path):
    repository = make_repository(tmp_path)
    ranking_id = repository.create_ranking(
        "Cafés", "", "position", "olive", "food"
    )
    repository.create_item(ranking_id, "A")
    repository.create_item(ranking_id, "B")
    repository.create_item(ranking_id, "C")

    repository.move_item(ranking_id, 2, 0)
    items = repository.list_items(ranking_id)

    assert [item.name for item in items] == ["C", "A", "B"]
    assert [item.position for item in items] == [0, 1, 2]


def test_insert_item_at_selected_position(tmp_path):
    repository = make_repository(tmp_path)
    ranking_id = repository.create_ranking(
        "Filmes", "", "position", "yellow", "star"
    )
    repository.create_item(ranking_id, "Primeiro")
    repository.create_item(ranking_id, "Terceiro")
    repository.create_item(ranking_id, "Segundo", position=1)

    items = repository.list_items(ranking_id)

    assert [item.name for item in items] == ["Primeiro", "Segundo", "Terceiro"]


def test_score_mode_orders_highest_first(tmp_path):
    repository = make_repository(tmp_path)
    ranking_id = repository.create_ranking(
        "Chocolates", "", "score", "pink", "food"
    )
    repository.create_item(ranking_id, "Sete", score=7.0)
    repository.create_item(ranking_id, "Nove", score=9.0)
    repository.create_item(ranking_id, "Oito", score=8.0)

    assert [item.name for item in repository.list_items(ranking_id)] == [
        "Nove",
        "Oito",
        "Sete",
    ]


def test_delete_item_closes_position_gap(tmp_path):
    repository = make_repository(tmp_path)
    ranking_id = repository.create_ranking(
        "Livros", "", "position", "blue", "book"
    )
    repository.create_item(ranking_id, "A")
    second_id = repository.create_item(ranking_id, "B")
    repository.create_item(ranking_id, "C")

    repository.delete_item(second_id)
    items = repository.list_items(ranking_id)

    assert [item.name for item in items] == ["A", "C"]
    assert [item.position for item in items] == [0, 1]


def test_migrates_existing_database_without_sort_mode(tmp_path):
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                color_key TEXT NOT NULL,
                icon_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE rank_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ranking_id INTEGER NOT NULL REFERENCES rankings(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                subtitle TEXT NOT NULL DEFAULT '',
                score REAL,
                note TEXT NOT NULL DEFAULT '',
                image_path TEXT,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            INSERT INTO rankings (
                name, description, color_key, icon_key, created_at, updated_at
            ) VALUES ('Teste antigo', '', 'blue', 'star', '2026-01-01', '2026-01-01');

            PRAGMA user_version = 1;
            """
        )

    repository = CatalogRepository(Database(database_path))
    rankings = repository.list_rankings()

    assert len(rankings) == 1
    assert rankings[0].name == "Teste antigo"
    assert rankings[0].sort_mode == "position"

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3


def test_preferences_are_persisted(tmp_path):
    repository = make_repository(tmp_path)

    assert repository.get_preference("language", "pt-BR") == "pt-BR"

    repository.set_preference("language", "en-US")

    assert repository.get_preference("language") == "en-US"

