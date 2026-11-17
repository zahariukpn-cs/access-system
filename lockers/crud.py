import json
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Card, Locker, Student



def add_student(s: Session, first_name: str, last_name: str) -> Student:
    student = Student(first_name=first_name, last_name=last_name)
    s.add(student)
    s.flush()
    return student


def add_card(s: Session, uid: bytes, student: Student) -> Card:
    card = Card(uid=uid, student_id=student.id)
    s.add(card)
    s.flush()
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


# ======================================================================
#  ПОШУК (повертають None, якщо нічого не знайдено)
# ======================================================================

def get_student(s: Session, student_id: int) -> Student | None:
    return s.get(Student, student_id)


def get_card(s: Session, uid: bytes) -> Card | None:
    return s.get(Card, uid)


def get_locker(s: Session, number: str) -> Locker | None:
    return s.scalar(select(Locker).where(Locker.number == number))


# ======================================================================
#  СПИСКИ
# ======================================================================

def list_students(s: Session) -> list[Student]:
    return list(s.scalars(select(Student).order_by(Student.id)))


def list_cards(s: Session) -> list[Card]:
    return list(s.scalars(select(Card).order_by(Card.student_id)))


def list_lockers(s: Session) -> list[Locker]:
    return list(s.scalars(select(Locker).order_by(Locker.number)))


def free_lockers(s: Session) -> list[Locker]:
    return list(s.scalars(select(Locker).where(~Locker.students.any())))


# ======================================================================
#  ВИДАЛЕННЯ
#  Видалення студента автоматично видаляє його картки та його доступи
#  до комірок (завдяки CASCADE в models.py). Видалення комірки прибирає
#  всі доступи до неї.
# ======================================================================

def delete_student(s: Session, student: Student) -> None:
    s.delete(student)
    s.flush()


def delete_card(s: Session, card: Card) -> None:
    s.delete(card)
    s.flush()


def delete_locker(s: Session, locker: Locker) -> None:
    s.delete(locker)
    s.flush()


# ======================================================================
#  ЕКСПОРТ ДЛЯ ЗЧИТУВАЧА
# ======================================================================

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
