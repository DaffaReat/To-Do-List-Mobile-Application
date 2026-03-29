from database.connection import db

def init_schema():
    conn = db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id   INTEGER REFERENCES nodes(id),
            title       TEXT    NOT NULL DEFAULT '',
            body        TEXT    NOT NULL DEFAULT '',
            state       TEXT    NOT NULL DEFAULT 'TODO'
                            CHECK(state IN ('TODO','DOING','DONE','CANCELLED')),
            position    INTEGER NOT NULL DEFAULT 0,
            scheduled   TEXT,
            deadline    TEXT,
            repeater    TEXT,
            created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
            title,
            body,
            content='nodes',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
            INSERT INTO nodes_fts(rowid, title, body)
            VALUES (new.id, new.title, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
            INSERT INTO nodes_fts(nodes_fts, rowid, title, body)
            VALUES ('delete', old.id, old.title, old.body);
            INSERT INTO nodes_fts(rowid, title, body)
            VALUES (new.id, new.title, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
            INSERT INTO nodes_fts(nodes_fts, rowid, title, body)
            VALUES ('delete', old.id, old.title, old.body);
        END;

        CREATE TRIGGER IF NOT EXISTS nodes_updated_at AFTER UPDATE ON nodes BEGIN
            UPDATE nodes SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
            WHERE id = new.id;
        END;
    """)
    conn.commit()
