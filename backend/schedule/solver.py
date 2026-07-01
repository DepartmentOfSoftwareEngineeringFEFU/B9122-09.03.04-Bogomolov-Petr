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
    def no_room_overlap(schedule, lesson, slot):
        for l in schedule.values():
            if l.get("day") == slot.day:
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
    """Решатель CSP (Backtracking + MCV/LCV)."""

    def __init__(self, lessons, slots=None, max_hours=36):
        self.lessons = lessons
        self.slots = slots or self._default_slots()
        self.max_hours = max_hours
        self.constraints = [
            ConstraintChecker.no_teacher_overlap,
            ConstraintChecker.no_class_overlap,
            ConstraintChecker.valid_time,
        ]
        self.teacher_subjects = defaultdict(set)

    def set_teacher_subjects(self, mapping):
        self.teacher_subjects = mapping

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

    def solve(self):
        schedule = {}
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
                unresolved.append(lesson)
                remaining.remove(lesson)

        return schedule, unresolved
