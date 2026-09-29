from datetime import datetime, timezone

from rank_everything.database import Database
from rank_everything.models import RankItem, Ranking


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CatalogRepository:
    def __init__(self, database: Database):
        self.database = database

    def get_preference(self, key: str, default: str | None = None) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_preferences WHERE key = ?",
                (key,),
            ).fetchone()
        return row["value"] if row else default

    def set_preference(self, key: str, value: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO app_preferences (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def create_ranking(
        self,
        name: str,
        description: str,
        sort_mode: str,
        color_key: str,
        icon_key: str,
    ) -> int:
        timestamp = now_iso()
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO rankings (
                    name, description, sort_mode, color_key, icon_key,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name.strip(),
                    description.strip(),
                    sort_mode,
                    color_key,
                    icon_key,
                    timestamp,
                    timestamp,
                ),
            )
            return int(cursor.lastrowid)

    def list_rankings(self, query: str = "") -> list[Ranking]:
        pattern = f"%{query.strip()}%"
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    r.*,
                    COUNT(i.id) AS item_count,
                    (
                        SELECT winner.name
                        FROM rank_items winner
                        JOIN rankings winner_ranking
                          ON winner_ranking.id = winner.ranking_id
                        WHERE winner.ranking_id = r.id
                        ORDER BY
                            CASE
                                WHEN winner_ranking.sort_mode = 'score'
                                THEN winner.score
                            END DESC,
                            winner.position ASC,
                            winner.id ASC
                        LIMIT 1
                    ) AS leader_name
                FROM rankings r
                LEFT JOIN rank_items i ON i.ranking_id = r.id
                WHERE r.name LIKE ? COLLATE NOCASE
                   OR r.description LIKE ? COLLATE NOCASE
                GROUP BY r.id
                ORDER BY r.updated_at DESC, r.id DESC
                """,
                (pattern, pattern),
            ).fetchall()
        return [self._ranking_from_row(row) for row in rows]

    def get_ranking(self, ranking_id: int) -> Ranking | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT r.*, COUNT(i.id) AS item_count, NULL AS leader_name
                FROM rankings r
                LEFT JOIN rank_items i ON i.ranking_id = r.id
                WHERE r.id = ?
                GROUP BY r.id
                """,
                (ranking_id,),
            ).fetchone()
        return self._ranking_from_row(row) if row else None

    def delete_ranking(self, ranking_id: int) -> None:
        with self.database.connect() as connection:
            connection.execute("DELETE FROM rankings WHERE id = ?", (ranking_id,))

    def create_item(
        self,
        ranking_id: int,
        name: str,
        subtitle: str = "",
        score: float | None = None,
        note: str = "",
        position: int | None = None,
    ) -> int:
        timestamp = now_iso()
        with self.database.connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM rank_items WHERE ranking_id = ?",
                (ranking_id,),
            ).fetchone()[0]
            insert_at = count if position is None else max(0, min(position, count))
            self._shift_positions(connection, ranking_id, insert_at, count - 1, 1)
            cursor = connection.execute(
                """
                INSERT INTO rank_items (
                    ranking_id, name, subtitle, score, note, image_path,
                    position, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    ranking_id,
                    name.strip(),
                    subtitle.strip(),
                    score,
                    note.strip(),
                    insert_at,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                "UPDATE rankings SET updated_at = ? WHERE id = ?",
                (timestamp, ranking_id),
            )
            return int(cursor.lastrowid)

    def list_items(self, ranking_id: int) -> list[RankItem]:
        ranking = self.get_ranking(ranking_id)
        if ranking is None:
            return []
        order_by = (
            "score DESC, position ASC, id ASC"
            if ranking.sort_mode == "score"
            else "position ASC, id ASC"
        )
        with self.database.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM rank_items WHERE ranking_id = ? ORDER BY {order_by}",
                (ranking_id,),
            ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def move_item(self, ranking_id: int, old_index: int, new_index: int) -> None:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT id
                FROM rank_items
                WHERE ranking_id = ?
                ORDER BY position ASC, id ASC
                """,
                (ranking_id,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            if not ids or old_index == new_index:
                return
            if old_index < 0 or old_index >= len(ids):
                raise IndexError("Posição de origem inválida")
            new_index = max(0, min(new_index, len(ids) - 1))
            moved = ids.pop(old_index)
            ids.insert(new_index, moved)
            connection.execute(
                "UPDATE rank_items SET position = position + 100000 WHERE ranking_id = ?",
                (ranking_id,),
            )
            for position, item_id in enumerate(ids):
                connection.execute(
                    "UPDATE rank_items SET position = ?, updated_at = ? WHERE id = ?",
                    (position, now_iso(), item_id),
                )
            connection.execute(
                "UPDATE rankings SET updated_at = ? WHERE id = ?",
                (now_iso(), ranking_id),
            )

    def delete_item(self, item_id: int) -> None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT ranking_id, position FROM rank_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if row is None:
                return
            connection.execute("DELETE FROM rank_items WHERE id = ?", (item_id,))
            connection.execute(
                """
                UPDATE rank_items
                SET position = position - 1
                WHERE ranking_id = ? AND position > ?
                """,
                (row["ranking_id"], row["position"]),
            )
            connection.execute(
                "UPDATE rankings SET updated_at = ? WHERE id = ?",
                (now_iso(), row["ranking_id"]),
            )

    @staticmethod
    def _shift_positions(connection, ranking_id: int, start: int, end: int, delta: int) -> None:
        if start > end:
            return
        connection.execute(
            """
            UPDATE rank_items
            SET position = position + 100000
            WHERE ranking_id = ? AND position BETWEEN ? AND ?
            """,
            (ranking_id, start, end),
        )
        connection.execute(
            """
            UPDATE rank_items
            SET position = position - 100000 + ?
            WHERE ranking_id = ? AND position BETWEEN ? AND ?
            """,
            (delta, ranking_id, start + 100000, end + 100000),
        )

    @staticmethod
    def _ranking_from_row(row) -> Ranking:
        return Ranking(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            sort_mode=row["sort_mode"],
            color_key=row["color_key"],
            icon_key=row["icon_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            item_count=row["item_count"],
            leader_name=row["leader_name"],
        )

    @staticmethod
    def _item_from_row(row) -> RankItem:
        return RankItem(
            id=row["id"],
            ranking_id=row["ranking_id"],
            name=row["name"],
            subtitle=row["subtitle"],
            score=row["score"],
            note=row["note"],
            image_path=row["image_path"],
            position=row["position"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

