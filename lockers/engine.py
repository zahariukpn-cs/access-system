from sqlalchemy import create_engine, event


def make_engine(path: str = "lockers.db"):
    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    return engine
