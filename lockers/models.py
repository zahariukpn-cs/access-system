from sqlalchemy import Column, ForeignKey, LargeBinary, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


locker_assignments = Table(
    "locker_assignments",
    Base.metadata,
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"),
           primary_key=True),
    Column("locker_id", ForeignKey("lockers.id", ondelete="CASCADE"),
           primary_key=True),
)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str]
    last_name: Mapped[str]

    cards: Mapped[list["Card"]] = relationship(
        back_populates="student", cascade="all, delete-orphan",
        passive_deletes=True)
    lockers: Mapped[list["Locker"]] = relationship(
        secondary=locker_assignments, back_populates="students",
        passive_deletes=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Locker(Base):
    __tablename__ = "lockers"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(unique=True)

    students: Mapped[list[Student]] = relationship(
        secondary=locker_assignments, back_populates="lockers",
        passive_deletes=True)


class Card(Base):
    __tablename__ = "cards"

    uid: Mapped[bytes] = mapped_column(LargeBinary, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"))

    student: Mapped[Student] = relationship(back_populates="cards")
