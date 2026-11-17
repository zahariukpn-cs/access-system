import sys
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateIndex, CreateTable

from .engine import make_engine
from .models import Base


def create_schema(path: str = "lockers.db") -> None:
    """Створює таблиці, яких ще немає. Існуючі не чіпає."""
    Base.metadata.create_all(make_engine(path))


def export_schema_sql(out: str = "schema.sql") -> None:
    """Пише чистий DDL у файл, без створення бази."""
    engine = create_engine("sqlite://")
    with open(out, "w", encoding="utf-8") as f:
        f.write("PRAGMA foreign_keys = ON;\n\n")
        for table in Base.metadata.sorted_tables:
            f.write(str(CreateTable(table).compile(engine)).strip() + ";\n\n")
            for index in table.indexes:
                f.write(str(CreateIndex(index).compile(engine)).strip() + ";\n\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"
    if cmd == "create":
        create_schema()
    elif cmd == "sql":
        export_schema_sql()
