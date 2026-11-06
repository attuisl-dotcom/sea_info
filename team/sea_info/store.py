from __future__ import annotations

import sqlite3
import secrets
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEED_POSTS = [
    ("제주 연안에서 만난 불가사리!", "바위 사이에서 만났어요. 색과 모양이 무척 인상적이었어요.", "불가사리", "바다탐험가", "제주", 24),
    ("소라게를 만났어요", "조수 웅덩이에서 작은 소라게를 관찰했습니다.", "소라게", "파도소리", "부산", 18),
    ("해변에서 만난 말미잘", "물에 닿지 않게 거리를 두고 관찰했어요.", "말미잘", "해변산책러", "강릉", 12),
    ("나의 첫 바다 관찰", "제주 바위 해안에서 불가사리를 만났어요.", "불가사리", "demo@sea-info.local", "제주", 3),
]


def connect(path: str | None = None) -> sqlite3.Connection:
    db = Path(path or os.getenv("SQLITE_PATH") or ROOT / "data" / "sea_info.sqlite3")
    if not db.is_absolute():
        db = ROOT / db
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def initialize(path: str | None = None) -> None:
    with connect(path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, body TEXT NOT NULL, species TEXT NOT NULL,
            author TEXT NOT NULL, region TEXT NOT NULL,
            board_type TEXT NOT NULL DEFAULT '자유 소통',
            location_visibility TEXT NOT NULL DEFAULT '비공개',
            is_public INTEGER NOT NULL DEFAULT 1,
            photo_public_consent INTEGER NOT NULL DEFAULT 0,
            operator_photo_consent INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, likes INTEGER NOT NULL DEFAULT 0,
            photo_blob BLOB
        );
        CREATE TABLE IF NOT EXISTS aquarium (
            user_id TEXT NOT NULL, species TEXT NOT NULL, first_seen TEXT NOT NULL,
            observation_id INTEGER, PRIMARY KEY(user_id, species),
            FOREIGN KEY(observation_id) REFERENCES observations(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS aquarium_visibility (
            user_id TEXT NOT NULL, species TEXT NOT NULL,
            is_public INTEGER NOT NULL DEFAULT 0 CHECK (is_public IN (0,1)),
            updated_at TEXT NOT NULL, PRIMARY KEY(user_id,species)
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, observation_id INTEGER NOT NULL,
            author TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY(observation_id) REFERENCES observations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS observation_likes (
            observation_id INTEGER NOT NULL, user_id TEXT NOT NULL,
            PRIMARY KEY(observation_id,user_id),
            FOREIGN KEY(observation_id) REFERENCES observations(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT, receipt TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
            email TEXT NOT NULL, status TEXT NOT NULL DEFAULT '접수', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            status TEXT NOT NULL, elapsed_ms INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            game TEXT NOT NULL, score INTEGER NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS point_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            source_type TEXT NOT NULL, source_id TEXT NOT NULL,
            points INTEGER NOT NULL, created_at TEXT NOT NULL,
            UNIQUE(user_id,source_type,source_id)
        );
        CREATE TABLE IF NOT EXISTS consent_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            observation_id INTEGER, consent_type TEXT NOT NULL, enabled INTEGER NOT NULL,
            notice_version TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)
        columns = {row[1] for row in con.execute("PRAGMA table_info(observations)")}
        if "photo_blob" not in columns:
            con.execute("ALTER TABLE observations ADD COLUMN photo_blob BLOB")
        if "is_public" not in columns:
            con.execute("ALTER TABLE observations ADD COLUMN is_public INTEGER NOT NULL DEFAULT 0")
        if "board_type" not in columns:
            con.execute("ALTER TABLE observations ADD COLUMN board_type TEXT NOT NULL DEFAULT '자유 소통'")
        if con.execute("SELECT COUNT(*) FROM observations").fetchone()[0] == 0:
            now = datetime.now(timezone.utc).isoformat()
            board_types = ["사진 이야기", "생물 질문방", "자유 소통", "관찰 모음"]
            for (title, body, species, author, region, likes), board_type in zip(SEED_POSTS, board_types):
                con.execute(
                    "INSERT INTO observations(title,body,species,author,region,board_type,created_at,likes,is_public) VALUES(?,?,?,?,?,?,?,?,1)",
                    (title, body, species, author, region, board_type, now, likes),
                )


def observations(path: str | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with connect(path) as con:
        return [dict(row) for row in con.execute("SELECT * FROM observations ORDER BY id DESC")]


def create_observation(*, title: str, body: str, species: str, author: str, region: str,
                       visibility: str, public_photo: bool, operator_photo: bool,
                       is_public: bool = True, board_type: str = "관찰 모음",
                       photo_blob: bytes | None = None, post_points: int = 0,
                       daily_points_cap: int = 50,
                       path: str | None = None) -> int:
    initialize(path)
    with connect(path) as con:
        now_dt = datetime.now(ZoneInfo("Asia/Seoul"))
        now = now_dt.isoformat()
        cur = con.execute("""INSERT INTO observations
            (title,body,species,author,region,board_type,location_visibility,is_public,photo_public_consent,
             operator_photo_consent,created_at,photo_blob)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (title.strip(), body.strip(), species, author, region, board_type, visibility, int(is_public),
             int(public_photo), int(operator_photo), now, photo_blob if public_photo else None))
        obs_id = int(cur.lastrowid)
        con.execute("INSERT OR IGNORE INTO aquarium(user_id,species,first_seen,observation_id) VALUES(?,?,?,?)",
                    (author, species, now, obs_id))
        for consent_type, enabled in (("public_post", is_public), ("public_photo", public_photo), ("operator_photo", operator_photo)):
            con.execute("INSERT INTO consent_history(user_id,observation_id,consent_type,enabled,notice_version,created_at) VALUES(?,?,?,?,?,?)",
                        (author, obs_id, consent_type, int(enabled), "1.0", now))
        if post_points and daily_points_cap > 0:
            earned_today = con.execute("SELECT COALESCE(SUM(points),0) FROM point_ledger WHERE user_id=? AND created_at LIKE ?",
                                       (author, now_dt.date().isoformat() + "%")).fetchone()[0]
            awarded = max(0, min(post_points, daily_points_cap - int(earned_today)))
        else:
            awarded = 0
        if awarded:
            con.execute("INSERT OR IGNORE INTO point_ledger(user_id,source_type,source_id,points,created_at) VALUES(?,?,?,?,?)",
                        (author, "observation", str(obs_id), awarded, now))
        return obs_id


def save_report(kind: str, title: str, body: str, email: str, path: str | None = None) -> str:
    initialize(path)
    receipt = "SI-" + secrets.token_hex(3).upper()
    with connect(path) as con:
        con.execute("INSERT INTO reports(receipt,kind,title,body,email,created_at) VALUES(?,?,?,?,?,?)",
                    (receipt, kind, title, body, email.strip().lower(), datetime.now(timezone.utc).isoformat()))
    return receipt


def lookup_report(receipt: str, email: str, path: str | None = None) -> dict[str, Any] | None:
    initialize(path)
    with connect(path) as con:
        row = con.execute("SELECT receipt,kind,title,status,created_at FROM reports WHERE receipt=? AND email=?",
                          (receipt.strip().upper(), email.strip().lower())).fetchone()
        return dict(row) if row else None


def list_reports(path: str | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with connect(path) as con:
        return [dict(row) for row in con.execute("SELECT * FROM reports ORDER BY id DESC")]


def update_report_status(receipt: str, status: str, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("UPDATE reports SET status=? WHERE receipt=?", (status, receipt))


def save_consent(user_id: str, consent_type: str, enabled: bool,
                 observation_id: int | None = None, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("INSERT INTO consent_history(user_id,observation_id,consent_type,enabled,notice_version,created_at) VALUES(?,?,?,?,?,?)",
                    (user_id, observation_id, consent_type, int(enabled), "1.0", datetime.now(timezone.utc).isoformat()))


def withdraw_species_photos(user_id: str, species: str, path: str | None = None) -> int:
    initialize(path)
    now = datetime.now(timezone.utc).isoformat()
    with connect(path) as con:
        rows = con.execute("SELECT id FROM observations WHERE author=? AND species=? AND photo_public_consent=1",
                           (user_id, species)).fetchall()
        ids = [row[0] for row in rows]
        if ids:
            con.executemany("UPDATE observations SET photo_public_consent=0,photo_blob=NULL WHERE id=?", [(i,) for i in ids])
            con.executemany("INSERT INTO consent_history(user_id,observation_id,consent_type,enabled,notice_version,created_at) VALUES(?,?,?,0,?,?)",
                            [(user_id, i, "public_photo", "1.0", now) for i in ids])
        return len(ids)


def aquarium_is_public(user_id: str, species: str, path: str | None = None) -> bool:
    initialize(path)
    with connect(path) as con:
        row=con.execute("SELECT is_public FROM aquarium_visibility WHERE user_id=? AND species=?",(user_id,species)).fetchone()
        return bool(row[0]) if row else False


def set_aquarium_public(user_id: str, species: str, enabled: bool, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("""INSERT INTO aquarium_visibility(user_id,species,is_public,updated_at) VALUES(?,?,?,?)
            ON CONFLICT(user_id,species) DO UPDATE SET is_public=excluded.is_public,updated_at=excluded.updated_at""",
            (user_id,species,int(enabled),datetime.now(ZoneInfo("Asia/Seoul")).isoformat()))


def public_species(user_id: str, path: str | None = None) -> list[str]:
    initialize(path)
    with connect(path) as con:
        return [row[0] for row in con.execute("SELECT species FROM aquarium_visibility WHERE user_id=? AND is_public=1 ORDER BY species",(user_id,))]


def add_comment(observation_id: int, author: str, body: str, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("INSERT INTO comments(observation_id,author,body,created_at) VALUES(?,?,?,?)",
                    (observation_id, author, body.strip(), datetime.now(timezone.utc).isoformat()))


def get_comments(observation_id: int, path: str | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with connect(path) as con:
        return [dict(r) for r in con.execute("SELECT * FROM comments WHERE observation_id=? ORDER BY id", (observation_id,))]


def update_observation(observation_id: int, owner: str, *, title: str, body: str,
                       visibility: str, is_public: bool, is_admin: bool = False,
                       path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        if is_admin:
            cur = con.execute("UPDATE observations SET title=?,body=?,location_visibility=?,is_public=? WHERE id=?",
                              (title.strip(), body.strip(), visibility, int(is_public), observation_id))
        else:
            cur = con.execute("UPDATE observations SET title=?,body=?,location_visibility=?,is_public=? WHERE id=? AND author=?",
                              (title.strip(), body.strip(), visibility, int(is_public), observation_id, owner))
        if cur.rowcount != 1:
            raise PermissionError("관찰 작성자만 수정할 수 있습니다.")


def delete_observation(observation_id: int, owner: str, *, is_admin: bool = False,
                       path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        row = con.execute("SELECT author,species FROM observations WHERE id=?", (observation_id,)).fetchone()
        if not row:
            raise PermissionError("관찰 기록을 찾을 수 없습니다.")
        if is_admin:
            cur = con.execute("DELETE FROM observations WHERE id=?", (observation_id,))
        else:
            cur = con.execute("DELETE FROM observations WHERE id=? AND author=?", (observation_id, owner))
        if cur.rowcount != 1:
            raise PermissionError("작성자 또는 운영자만 삭제할 수 있습니다.")
        points = con.execute("SELECT points FROM point_ledger WHERE user_id=? AND source_type='observation' AND source_id=?",
                             (row["author"], str(observation_id))).fetchone()
        if points and points[0]:
            con.execute("INSERT OR IGNORE INTO point_ledger(user_id,source_type,source_id,points,created_at) VALUES(?,?,?,?,?)",
                        (row["author"], "observation_delete", str(observation_id), -int(points[0]), datetime.now(ZoneInfo("Asia/Seoul")).isoformat()))
        remaining = con.execute("SELECT id FROM observations WHERE author=? AND species=? ORDER BY id DESC LIMIT 1", (row["author"], row["species"])).fetchone()
        if not remaining:
            con.execute("DELETE FROM aquarium WHERE user_id=? AND species=?", (row["author"], row["species"]))
            con.execute("DELETE FROM aquarium_visibility WHERE user_id=? AND species=?", (row["author"], row["species"]))
        else:
            con.execute("UPDATE aquarium SET observation_id=? WHERE user_id=? AND species=?",
                        (remaining[0], row["author"], row["species"]))


def toggle_like(observation_id: int, user_id: str, path: str | None = None) -> bool:
    initialize(path)
    with connect(path) as con:
        cur = con.execute("DELETE FROM observation_likes WHERE observation_id=? AND user_id=?", (observation_id, user_id))
        if cur.rowcount:
            con.execute("UPDATE observations SET likes=MAX(0,likes-1) WHERE id=?", (observation_id,))
            return False
        con.execute("INSERT INTO observation_likes(observation_id,user_id) VALUES(?,?)", (observation_id, user_id))
        con.execute("UPDATE observations SET likes=likes+1 WHERE id=?", (observation_id,))
        return True


def save_game(user_id: str, game: str, score: int, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("INSERT INTO game_results(user_id,game,score,created_at) VALUES(?,?,?,?)",
                    (user_id, game, score, datetime.now(timezone.utc).isoformat()))


def get_points(user_id: str, path: str | None = None) -> int:
    initialize(path)
    with connect(path) as con:
        row = con.execute("SELECT COALESCE(SUM(points),0) FROM point_ledger WHERE user_id=?", (user_id,)).fetchone()
        return int(row[0])


def game_top(game: str, path: str | None = None) -> list[dict[str, Any]]:
    initialize(path)
    with connect(path) as con:
        rows=con.execute("""SELECT user_id,MAX(score) AS score,MIN(created_at) AS achieved_at
            FROM game_results WHERE game=? GROUP BY user_id
            ORDER BY score DESC,achieved_at ASC LIMIT 5""", (game,)).fetchall()
        return [dict(row) for row in rows]


def log_analysis(user_id: str, status: str, elapsed_ms: int, path: str | None = None) -> None:
    initialize(path)
    with connect(path) as con:
        con.execute("INSERT INTO ai_logs(user_id,status,elapsed_ms,created_at) VALUES(?,?,?,?)",
                    (user_id, status, max(0, elapsed_ms), datetime.now(timezone.utc).isoformat()))
