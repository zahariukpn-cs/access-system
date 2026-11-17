"""
Адмінська програма системи контролю доступу (консольна версія).

Запуск:   python main.py
Потрібно: pip install sqlalchemy   (версія 2.x)

Що робить програма:
  1. Створює файл бази lockers.db з таблицями (якщо його ще немає).
  2. Чекає команди від адміна (add student, add card, assign, ...).
  3. Кожну команду, що щось змінює, записує у файл (commit).
  4. Після кожної зміни оновлює snapshot.json -- файл для зчитувача.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from lockers import crud
from lockers.engine import make_engine
from lockers.migrate import create_schema, export_schema_sql

DB_PATH = "lockers.db"          # файл бази даних
SNAPSHOT_PATH = "snapshot.json"  # файл для програми-зчитувача
AUTO_SNAPSHOT = True            # оновлювати snapshot.json після кожної зміни

HELP_TEXT = """
Команди (<...> -- це те, що треба підставити):

  add student <ім'я> <прізвище>     додати студента
  add card <uid> <id студента>      додати картку студенту (uid -- hex, напр. 04a1b2c3)
  add locker <номер>                додати комірку (напр. A12)

  assign <id студента> <номер комірки>     дати студенту доступ до комірки
  unassign <id студента> <номер комірки>   забрати доступ

  delete student <id>               видалити студента (разом з картками і доступами)
  delete card <uid>                 видалити картку
  delete locker <номер>             видалити комірку

  list students                     показати всіх студентів
  list cards                        показати всі картки
  list lockers                      показати всі комірки
  list free                         показати комірки, до яких ніхто не має доступу

  snapshot                          записати snapshot.json вручну
  schema                            записати schema.sql (код створення таблиць)
  help                              ця підказка
  exit                              вийти
"""


class CommandError(Exception):
    """Помилка, яку треба показати адміну (наприклад, 'студента не знайдено')."""


# ----------------------------------------------------------------------
#  Допоміжні функції: перетворити текст від адміна на потрібні значення
# ----------------------------------------------------------------------

def parse_uid(text: str) -> bytes:
    """'04:a1:b2:c3' або '04a1b2c3' -> байти. Так UID зберігається в базі."""
    cleaned = text.replace(":", "").replace(" ", "")
    try:
        uid = bytes.fromhex(cleaned)
    except ValueError:
        raise CommandError("UID має складатися з hex-символів (0-9, a-f), напр. 04a1b2c3")
    if not uid:
        raise CommandError("UID не може бути порожнім")
    return uid


def need_student(s: Session, text: str):
    """Знайти студента за id або сказати адміну, що його немає."""
    try:
        student_id = int(text)
    except ValueError:
        raise CommandError("id студента має бути числом")
    student = crud.get_student(s, student_id)
    if student is None:
        raise CommandError(f"Студента з id {student_id} не існує")
    return student


def need_locker(s: Session, number: str):
    locker = crud.get_locker(s, number)
    if locker is None:
        raise CommandError(f"Комірки {number} не існує")
    return locker


def need_card(s: Session, text: str):
    card = crud.get_card(s, parse_uid(text))
    if card is None:
        raise CommandError(f"Картки {text} не існує")
    return card


def confirm(question: str) -> bool:
    return input(f"{question} (y/n): ").strip().lower() in ("y", "yes", "так", "т")


def usage(text: str):
    raise CommandError(f"Використання: {text}")


# ----------------------------------------------------------------------
#  Команди. Кожна приймає (s, args) і повертає текст-відповідь.
#  s    -- сесія (з'єднання з базою)
#  args -- слова після назви команди
# ----------------------------------------------------------------------

def cmd_add_student(s, args):
    if len(args) < 2:
        usage("add student <ім'я> <прізвище>")
    student = crud.add_student(s, args[0], " ".join(args[1:]))
    return f"Студента додано, id = {student.id}"


def cmd_add_card(s, args):
    if len(args) != 2:
        usage("add card <uid> <id студента>")
    uid = parse_uid(args[0])
    student = need_student(s, args[1])
    existing = crud.get_card(s, uid)
    if existing is not None:
        raise CommandError(
            f"Така картка вже є (належить студенту {existing.student.full_name}, "
            f"id = {existing.student_id})")
    crud.add_card(s, uid, student)
    return f"Картку {uid.hex()} прив'язано до студента {student.full_name}"


def cmd_add_locker(s, args):
    if len(args) != 1:
        usage("add locker <номер>")
    if crud.get_locker(s, args[0]) is not None:
        raise CommandError(f"Комірка {args[0]} вже існує")
    locker = crud.add_locker(s, args[0])
    return f"Комірку {locker.number} додано"


def cmd_assign(s, args):
    if len(args) != 2:
        usage("assign <id студента> <номер комірки>")
    student = need_student(s, args[0])
    locker = need_locker(s, args[1])
    if student in locker.students:
        return f"{student.full_name} вже має доступ до {locker.number}"
    crud.assign_locker(locker, student)
    return f"{student.full_name} тепер має доступ до {locker.number}"


def cmd_unassign(s, args):
    if len(args) != 2:
        usage("unassign <id студента> <номер комірки>")
    student = need_student(s, args[0])
    locker = need_locker(s, args[1])
    if student not in locker.students:
        return f"{student.full_name} і так не мав доступу до {locker.number}"
    crud.unassign_locker(locker, student)
    return f"Доступ {student.full_name} до {locker.number} забрано"


def cmd_delete_student(s, args):
    if len(args) != 1:
        usage("delete student <id>")
    student = need_student(s, args[0])
    question = (f"Видалити {student.full_name}? Разом зникнуть його картки "
                f"({len(student.cards)}) і доступи до комірок ({len(student.lockers)})")
    if not confirm(question):
        return "Скасовано"
    name = student.full_name
    crud.delete_student(s, student)
    return f"Студента {name} видалено"


def cmd_delete_card(s, args):
    if len(args) != 1:
        usage("delete card <uid>")
    card = need_card(s, args[0])
    if not confirm(f"Видалити картку {card.uid.hex()}?"):
        return "Скасовано"
    uid_hex = card.uid.hex()
    crud.delete_card(s, card)
    return f"Картку {uid_hex} видалено"


def cmd_delete_locker(s, args):
    if len(args) != 1:
        usage("delete locker <номер>")
    locker = need_locker(s, args[0])
    if not confirm(f"Видалити комірку {locker.number}? Усі доступи до неї зникнуть "
                   f"({len(locker.students)})"):
        return "Скасовано"
    number = locker.number
    crud.delete_locker(s, locker)
    return f"Комірку {number} видалено"


def cmd_list_students(s, args):
    students = crud.list_students(s)
    if not students:
        return "Студентів ще немає"
    lines = []
    for st in students:
        lockers = ", ".join(sorted(l.number for l in st.lockers)) or "-"
        cards = ", ".join(c.uid.hex() for c in st.cards) or "-"
        lines.append(f"  {st.id:>3}  {st.full_name:<25} комірки: {lockers:<15} картки: {cards}")
    return "\n".join(lines)


def cmd_list_cards(s, args):
    cards = crud.list_cards(s)
    if not cards:
        return "Карток ще немає"
    return "\n".join(
        f"  {c.uid.hex():<20} -> {c.student.full_name} (id {c.student_id})"
        for c in cards)


def cmd_list_lockers(s, args):
    lockers = crud.list_lockers(s)
    if not lockers:
        return "Комірок ще немає"
    lines = []
    for l in lockers:
        who = ", ".join(st.full_name for st in l.students) or "ніхто"
        lines.append(f"  {l.number:<10} доступ: {who}")
    return "\n".join(lines)


def cmd_list_free(s, args):
    lockers = crud.free_lockers(s)
    if not lockers:
        return "Вільних комірок немає"
    return "Вільні комірки: " + ", ".join(l.number for l in lockers)


def write_snapshot(s):
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        f.write(crud.export_snapshot(s))


def cmd_snapshot(s, args):
    write_snapshot(s)
    return f"Записано {SNAPSHOT_PATH}"


def cmd_schema(s, args):
    export_schema_sql("schema.sql")
    return "Записано schema.sql"


def cmd_help(s, args):
    return HELP_TEXT


# Таблиця команд:  "назва" -> (функція, чи змінює вона базу)
# Якщо змінює -- після неї робимо commit (зберігаємо у файл).
COMMANDS = {
    "add student":    (cmd_add_student, True),
    "add card":       (cmd_add_card, True),
    "add locker":     (cmd_add_locker, True),
    "assign":         (cmd_assign, True),
    "unassign":       (cmd_unassign, True),
    "delete student": (cmd_delete_student, True),
    "delete card":    (cmd_delete_card, True),
    "delete locker":  (cmd_delete_locker, True),
    "list students":  (cmd_list_students, False),
    "list cards":     (cmd_list_cards, False),
    "list lockers":   (cmd_list_lockers, False),
    "list free":      (cmd_list_free, False),
    "snapshot":       (cmd_snapshot, False),
    "schema":         (cmd_schema, False),
    "help":           (cmd_help, False),
}

# Команди з двох слів ("add student") і з одного ("assign")
TWO_WORD_PREFIXES = {"add", "delete", "list"}


def find_command(words):
    """Розпізнати команду. Повертає (назва, решта слів) або (None, [])."""
    if words[0] in TWO_WORD_PREFIXES and len(words) >= 2:
        name = f"{words[0]} {words[1]}"
        return (name, words[2:]) if name in COMMANDS else (None, [])
    if words[0] in COMMANDS:
        return words[0], words[1:]
    return None, []


# ----------------------------------------------------------------------
#  Головний цикл
# ----------------------------------------------------------------------

def main():
    create_schema(DB_PATH)          # створює lockers.db і таблиці, якщо їх немає
    engine = make_engine(DB_PATH)   # з'єднання з файлом бази

    print("Адмінка системи контролю доступу. Напиши 'help' для списку команд.")

    with Session(engine) as s:      # сесія = "чернетка" змін, поки не зроблено commit
        if AUTO_SNAPSHOT:
            write_snapshot(s)

        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue
            if line.lower() in ("exit", "quit", "вихід"):
                break

            words = line.split()
            words[0] = words[0].lower()
            if words[0] in TWO_WORD_PREFIXES and len(words) >= 2:
                words[1] = words[1].lower()

            name, args = find_command(words)
            if name is None:
                print("Невідома команда. Напиши 'help'.")
                continue

            handler, changes_db = COMMANDS[name]
            try:
                message = handler(s, args)
                if changes_db:
                    s.commit()                  # <-- ось тут зміни потрапляють у файл
                    if AUTO_SNAPSHOT:
                        write_snapshot(s)
                print(message)
            except CommandError as e:
                s.rollback()                    # скасувати недороблені зміни
                print(f"Помилка: {e}")
            except IntegrityError as e:
                s.rollback()
                print(f"Помилка бази даних: {e.orig}")


if __name__ == "__main__":
    main()
