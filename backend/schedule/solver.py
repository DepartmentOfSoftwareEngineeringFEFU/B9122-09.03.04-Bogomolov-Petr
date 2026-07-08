import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import time


@dataclass
class TimeSlot:
    day: int
    start: time
    end: time


@dataclass
class LessonVar:
    id: int
    subject_id: int
    class_id: int
    teacher_id: int
    duration_minutes: int = 45
    domain: list = field(default_factory=list)


class ConstraintChecker:
    """Проверка ограничений C1–C7."""

    @staticmethod
    def no_teacher_overlap(schedule, lesson, slot):
        for l in schedule.values():
            if (
                l.get("teacher_id") == lesson.teacher_id
                and l.get("day") == slot.day
            ):
                if not (slot.end <= l["start"] or slot.start >= l["end"]):
                    return False
        return True

    @staticmethod
    def no_class_overlap(schedule, lesson, slot):
        for l in schedule.values():
            if (
                l.get("class_id") == lesson.class_id
                and l.get("day") == slot.day
            ):
                if not (slot.end <= l["start"] or slot.start >= l["end"]):
                    return False
        return True

    @staticmethod
    def valid_time(schedule, lesson, slot):
        return slot.start < slot.end

    @staticmethod
    def correct_teacher(lesson, teacher_subjects):
        return lesson.subject_id in teacher_subjects.get(
            lesson.teacher_id, set()
        )

    @staticmethod
    def workload_ok(schedule, lesson, slot, max_hours):
        total = 0
        for l in schedule.values():
            if l.get("teacher_id") == lesson.teacher_id:
                total += (l["end"].hour + l["end"].minute / 60) - (
                    l["start"].hour + l["start"].minute / 60
                )
        new = (slot.end.hour + slot.end.minute / 60) - (
            slot.start.hour + slot.start.minute / 60
        )
        return total + new <= max_hours

    @staticmethod
    def no_room_overlap(schedule, lesson, slot, class_rooms=None):
        """C7: два занятия разных классов с одинаковой аудиторией по
        умолчанию не могут пересекаться по времени. Без переданной карты
        class_rooms (class_id -> аудитория) ограничение не применяется."""
        if lesson is None or not class_rooms:
            return True
        room = class_rooms.get(lesson.class_id)
        if not room:
            return True
        for l in schedule.values():
            if l.get("day") != slot.day:
                continue
            other_class = l.get("class_id")
            if other_class == lesson.class_id:
                continue
            if class_rooms.get(other_class) != room:
                continue
            if not (slot.end <= l["start"] or slot.start >= l["end"]):
                return False
        return True


class VariableSelector:
    """Эвристика MCV — выбор самого ограниченного занятия."""

    @staticmethod
    def select(
        schedule, lessons, slots, constraints, teacher_subjects, max_hours
    ):
        best = None
        min_domain = float("inf")
        for lesson in lessons:
            if lesson.id in schedule:
                continue
            count = 0
            for slot in slots:
                if all(c(schedule, lesson, slot) for c in constraints):
                    count += 1
            if count < min_domain:
                min_domain = count
                best = lesson
                if count == 0:
                    break
        return best


class ValueSelector:
    """Эвристика LCV — сортировка слотов по наименьшим ограничениям."""

    @staticmethod
    def order(schedule, lesson, slots, lessons, constraints):
        def conflicts(slot):
            count = 0
            temp = dict(schedule)
            temp[lesson.id] = {
                "teacher_id": lesson.teacher_id,
                "class_id": lesson.class_id,
                "day": slot.day,
                "start": slot.start,
                "end": slot.end,
            }
            for other in lessons:
                if other.id in temp or other.id == lesson.id:
                    continue
                for s in [
                    TimeSlot(day=slot.day, start=slot.start, end=slot.end)
                ]:
                    if not all(c(temp, other, s) for c in constraints):
                        count += 1
                        break
            return count

        return sorted(slots, key=conflicts)


class ScheduleSolver:
    """Решатель CSP (Backtracking + MCV/LCV) с ограничениями C1–C7."""

    CONSTRAINT_LABELS = {
        "no_teacher_overlap": "преподаватель уже занят в это время другим занятием",
        "no_class_overlap": "класс уже занят другим занятием в это время",
        "valid_time": "некорректный временной интервал",
        "correct_teacher": "преподаватель не ведёт данную дисциплину",
        "workload_ok": "превышена недельная норма часов преподавателя",
        "no_room_overlap": "аудитория класса занята другим классом в это время",
    }

    def __init__(self, lessons, slots=None, max_hours=36):
        self.lessons = lessons
        self.slots = slots or self._default_slots()
        # max_hours: либо общее число часов на всех, либо словарь {teacher_id: часы}
        self.max_hours = max_hours
        self.teacher_subjects = defaultdict(set)
        self.class_rooms = {}
        self.constraints = self._build_constraints()

    def set_teacher_subjects(self, mapping):
        self.teacher_subjects = mapping

    def set_class_rooms(self, mapping):
        """C7: карта {class_id: аудитория}, используемая при проверке пересечения аудиторий."""
        self.class_rooms = mapping

    def _max_hours_for(self, teacher_id):
        if isinstance(self.max_hours, dict):
            return self.max_hours.get(teacher_id, 36)
        return self.max_hours

    def _build_constraints(self):
        def correct_teacher(schedule, lesson, slot):
            return ConstraintChecker.correct_teacher(lesson, self.teacher_subjects)

        def workload_ok(schedule, lesson, slot):
            return ConstraintChecker.workload_ok(
                schedule, lesson, slot, self._max_hours_for(lesson.teacher_id)
            )

        def no_room_overlap(schedule, lesson, slot):
            return ConstraintChecker.no_room_overlap(
                schedule, lesson, slot, self.class_rooms
            )

        return [
            ConstraintChecker.no_teacher_overlap,
            ConstraintChecker.no_class_overlap,
            ConstraintChecker.valid_time,
            correct_teacher,
            workload_ok,
            no_room_overlap,
        ]

    @staticmethod
    def _default_slots():
        slots = []
        days = range(1, 7)
        hours = [
            (time(8, 0), time(8, 45)),
            (time(8, 55), time(9, 40)),
            (time(9, 50), time(10, 35)),
            (time(10, 45), time(11, 30)),
            (time(11, 40), time(12, 25)),
            (time(12, 35), time(13, 20)),
            (time(13, 30), time(14, 15)),
        ]
        for day in days:
            for start, end in hours:
                slots.append(TimeSlot(day=day, start=start, end=end))
        return slots

    def diagnose(self, lesson, schedule):
        """SCH_03: определяет, какие ограничения не позволяют разместить
        занятие ни в один слот, и возвращает человекочитаемые причины."""
        reasons = []
        for c in self.constraints:
            others = [x for x in self.constraints if x is not c]
            sole_blocker = any(
                all(x(schedule, lesson, slot) for x in others) and not c(schedule, lesson, slot)
                for slot in self.slots
            )
            if sole_blocker:
                reasons.append(self.CONSTRAINT_LABELS.get(c.__name__, c.__name__))
        if not reasons:
            reasons.append(
                "нет свободного слота, одновременно удовлетворяющего всем ограничениям"
            )
        return reasons

    def solve(self, preassigned=None):
        """Решает CSP. preassigned — уже существующие занятия (для режима
        дозаполнения), учитываются при проверке ограничений, но не
        возвращаются в результате — возвращаются только новые назначения."""
        schedule = dict(preassigned or {})
        locked_keys = set(schedule.keys())
        unresolved = []
        remaining = list(self.lessons)
        random.shuffle(remaining)
        random.shuffle(self.slots)
        max_iter = len(self.lessons) * 100
        iteration = 0

        while remaining and iteration < max_iter:
            iteration += 1
            lesson = VariableSelector.select(
                schedule,
                remaining,
                self.slots,
                self.constraints,
                self.teacher_subjects,
                self.max_hours,
            )
            if lesson is None:
                break

            ordered = ValueSelector.order(
                schedule, lesson, self.slots, remaining, self.constraints
            )
            assigned = False
            for slot in ordered:
                if all(c(schedule, lesson, slot) for c in self.constraints):
                    schedule[lesson.id] = {
                        "lesson_id": lesson.id,
                        "subject_id": lesson.subject_id,
                        "teacher_id": lesson.teacher_id,
                        "class_id": lesson.class_id,
                        "day": slot.day,
                        "start": slot.start,
                        "end": slot.end,
                    }
                    remaining.remove(lesson)
                    assigned = True
                    break

            if not assigned:
                unresolved.append({
                    "lesson": lesson,
                    "reasons": self.diagnose(lesson, schedule),
                })
                remaining.remove(lesson)

        new_schedule = {k: v for k, v in schedule.items() if k not in locked_keys}
        return new_schedule, unresolved
