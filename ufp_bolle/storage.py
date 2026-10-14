"""Persistenza locale privata. Il registro non costituisce prova del gestionale."""

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def private_parent(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def connect(path, role):
    path = private_parent(path)
    # Crea il file privato prima che SQLite lo apra; non cambia il suo contenuto.
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.close(fd)
    os.chmod(path, 0o600)
    con = sqlite3.connect(path, timeout=2)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA synchronous=FULL")
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if tables and "ufp_metadata" not in tables:
        con.close()
        raise ValueError("Database non UFP: usare un nuovo percorso dedicato.")
    con.execute("CREATE TABLE IF NOT EXISTS ufp_metadata (role TEXT PRIMARY KEY)")
    roles = [r[0] for r in con.execute("SELECT role FROM ufp_metadata")]
    if roles and roles != [role]:
        con.close()
        raise ValueError("Database con ruolo diverso: registro e simulatore devono essere separati.")
    con.execute("INSERT OR IGNORE INTO ufp_metadata VALUES (?)", (role,))
    con.commit()
    return con


@contextmanager
def single_operator(path):
    lock = private_parent(str(Path(path).resolve()) + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("Lavorazione già aperta o lock residuo. Verificare il processo prima di rimuovere il file .lock.") from None
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def write_json(path, value):
    path = private_parent(path)
    # Non sovrascrive una verifica precedente: ogni revisione ha un proprio file.
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON con chiavi duplicate: correggere il file.")
            result[key] = value
        return result
    # Alcuni editor Windows aggiungono un BOM: non è parte dei dati JSON.
    with open(path, encoding="utf-8-sig") as stream:
        return json.load(stream, object_pairs_hook=unique_pairs)
