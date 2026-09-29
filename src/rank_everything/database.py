import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version < 1:
                connection.executescript(
                    """
                    CREATE TABLE rankings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 60),
                        description TEXT NOT NULL DEFAULT '',
                        sort_mode TEXT NOT NULL CHECK(sort_mode IN ('position', 'score')),
                        color_key TEXT NOT NULL,
                        icon_key TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE TABLE rank_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ranking_id INTEGER NOT NULL REFERENCES rankings(id) ON DELETE CASCADE,
                        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 80),
                        subtitle TEXT NOT NULL DEFAULT '',
                        score REAL CHECK(score IS NULL OR score BETWEEN 0 AND 10),
                        note TEXT NOT NULL DEFAULT '',
                        image_path TEXT,
                        position INTEGER NOT NULL CHECK(position >= 0),
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE UNIQUE INDEX rank_items_position
                    ON rank_items(ranking_id, position);

                    CREATE INDEX rankings_updated_at
                    ON rankings(updated_at DESC);

                    PRAGMA user_version = 1;
                    """
                )

            ranking_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(rankings)").fetchall()
            }
            if "sort_mode" not in ranking_columns:
                connection.execute(
                    """
                    ALTER TABLE rankings
                    ADD COLUMN sort_mode TEXT NOT NULL DEFAULT 'position'
                    CHECK(sort_mode IN ('position', 'score'))
                    """
                )

            if version < 3:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                    """
                )

            connection.execute("PRAGMA user_version = 3")

