import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Card, Locker, Student


def make_engine(path: str = "lockers.db"):
    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(engine)
    return engine


def add_student(s: Session, first_name: str, last_name: str) -> Student:
    student = Student(first_name=first_name, last_name=last_name)
    s.add(student)
    s.flush()
    return student


def add_card(s: Session, uid: bytes, student: Student) -> Card:
    card = Card(uid=uid, student_id=student.id)
    s.add(card)
    return card


def add_locker(s: Session, number: str) -> Locker:
    locker = Locker(number=number)
    s.add(locker)
    s.flush()
    return locker


def assign_locker(locker: Locker, student: Student) -> None:
    if student not in locker.students:
        locker.students.append(student)


def unassign_locker(locker: Locker, student: Student) -> None:
    if student in locker.students:
        locker.students.remove(student)


def free_lockers(s: Session) -> list[Locker]:
    return list(s.scalars(select(Locker).where(~Locker.students.any())))


def export_snapshot(s: Session) -> str:
    cards = {c.uid.hex(): c.student_id for c in s.scalars(select(Card))}

    students = {}
    for st in s.scalars(select(Student)):
        students[str(st.id)] = {
            "name": st.full_name,
            "lockers": [l.number for l in st.lockers],
        }

    return json.dumps(
        {"version": int(time.time()), "cards": cards, "students": students},
        ensure_ascii=False, separators=(",", ":"),
    )
