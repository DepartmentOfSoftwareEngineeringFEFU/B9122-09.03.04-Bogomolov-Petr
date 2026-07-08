from datetime import time

from django.test import Client, TestCase
from django.urls import reverse

from schedule.solver import (ConstraintChecker, LessonVar, ScheduleSolver,
                              TimeSlot, VariableSelector, ValueSelector)


class ConstraintCheckerTest(TestCase):
    def setUp(self):
        self.slot1 = TimeSlot(day=1, start=time(8, 0), end=time(8, 45))
        self.slot2 = TimeSlot(day=1, start=time(8, 55), end=time(9, 40))
        self.slot3 = TimeSlot(day=1, start=time(8, 30), end=time(9, 15))
        self.slot4 = TimeSlot(day=2, start=time(8, 0), end=time(8, 45))
        self.lesson = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        self.lesson2 = LessonVar(id=2, subject_id=2, class_id=2, teacher_id=1)

    def test_valid_time_true(self):
        self.assertTrue(ConstraintChecker.valid_time({}, None, self.slot1))

    def test_valid_time_start_equals_end(self):
        slot = TimeSlot(day=1, start=time(8, 0), end=time(8, 0))
        self.assertFalse(ConstraintChecker.valid_time({}, None, slot))

    def test_valid_time_end_before_start(self):
        slot = TimeSlot(day=1, start=time(9, 0), end=time(8, 0))
        self.assertFalse(ConstraintChecker.valid_time({}, None, slot))

    def test_no_teacher_overlap_no_collision(self):
        schedule = {}
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, self.lesson, self.slot1))

    def test_no_teacher_overlap_same_time(self):
        schedule = {
            2: {
                'teacher_id': 1, 'class_id': 2, 'day': 1,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        self.assertFalse(ConstraintChecker.no_teacher_overlap(schedule, self.lesson, self.slot1))

    def test_no_teacher_overlap_different_day(self):
        schedule = {
            2: {
                'teacher_id': 1, 'class_id': 2, 'day': 2,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, self.lesson, self.slot1))

    def test_no_teacher_overlap_different_teacher(self):
        schedule = {
            2: {
                'teacher_id': 2, 'class_id': 2, 'day': 1,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, self.lesson, self.slot1))

    def test_no_teacher_overlap_adjacent_slots(self):
        schedule = {
            2: {
                'teacher_id': 1, 'class_id': 2, 'day': 1,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, self.lesson, self.slot2))

    def test_no_class_overlap(self):
        schedule = {}
        self.assertTrue(ConstraintChecker.no_class_overlap(schedule, self.lesson, self.slot1))

    def test_no_class_overlap_collision(self):
        schedule = {
            2: {
                'teacher_id': 2, 'class_id': 1, 'day': 1,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        self.assertFalse(ConstraintChecker.no_class_overlap(schedule, self.lesson, self.slot1))

    def test_correct_teacher(self):
        teacher_subjects = {1: {1, 2}}
        self.assertTrue(ConstraintChecker.correct_teacher(self.lesson, teacher_subjects))

    def test_correct_teacher_wrong(self):
        teacher_subjects = {1: {3}}
        self.assertFalse(ConstraintChecker.correct_teacher(self.lesson, teacher_subjects))

    def test_workload_ok(self):
        schedule = {}
        self.assertTrue(ConstraintChecker.workload_ok(schedule, self.lesson, self.slot1, 36))

    def test_workload_exceeded(self):
        schedule = {}
        self.assertFalse(ConstraintChecker.workload_ok(schedule, self.lesson, self.slot1, 0))

    def test_room_overlap(self):
        schedule = {}
        self.assertTrue(ConstraintChecker.no_room_overlap(schedule, None, self.slot1))


class CSPConstraintTest(TestCase):
    """Integration test for constraints C1-C7 as described in diploma."""

    def test_c1_no_teacher_overlap(self):
        """C1: непересекаемость преподавателя."""
        slot1 = TimeSlot(day=1, start=time(8, 0), end=time(8, 45))
        slot2 = TimeSlot(day=1, start=time(8, 30), end=time(9, 15))
        slot3 = TimeSlot(day=1, start=time(8, 55), end=time(9, 40))
        schedule = {}
        lesson1 = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        lesson2 = LessonVar(id=2, subject_id=2, class_id=2, teacher_id=1)
        # No conflict with empty schedule
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, lesson1, slot1))
        schedule[1] = {'teacher_id': 1, 'class_id': 1, 'day': 1, 'start': slot1.start, 'end': slot1.end}
        # Same teacher, overlapping time → conflict
        self.assertFalse(ConstraintChecker.no_teacher_overlap(schedule, lesson2, slot2))
        # Same teacher, non-overlapping time → ok
        self.assertTrue(ConstraintChecker.no_teacher_overlap(schedule, lesson2, slot3))

    def test_c2_no_class_overlap(self):
        """C2: занятость класса."""
        slot1 = TimeSlot(day=1, start=time(8, 0), end=time(8, 45))
        slot2 = TimeSlot(day=1, start=time(8, 30), end=time(9, 15))
        schedule = {}
        lesson1 = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        lesson2 = LessonVar(id=2, subject_id=2, class_id=1, teacher_id=2)
        self.assertTrue(ConstraintChecker.no_class_overlap(schedule, lesson1, slot1))
        schedule[1] = {'teacher_id': 1, 'class_id': 1, 'day': 1, 'start': slot1.start, 'end': slot1.end}
        self.assertFalse(ConstraintChecker.no_class_overlap(schedule, lesson2, slot2))

    def test_c3_valid_time(self):
        """C3: корректность времени."""
        self.assertTrue(ConstraintChecker.valid_time({}, None, TimeSlot(day=1, start=time(8, 0), end=time(8, 45))))
        self.assertFalse(ConstraintChecker.valid_time({}, None, TimeSlot(day=1, start=time(8, 0), end=time(8, 0))))
        self.assertFalse(ConstraintChecker.valid_time({}, None, TimeSlot(day=1, start=time(9, 0), end=time(8, 0))))

    def test_c4_correct_teacher(self):
        """C4: соответствие преподавателя."""
        teacher_subjects = {1: {1, 2}, 2: {3}}
        lesson1 = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        lesson2 = LessonVar(id=2, subject_id=3, class_id=1, teacher_id=2)
        lesson3 = LessonVar(id=3, subject_id=1, class_id=1, teacher_id=2)
        self.assertTrue(ConstraintChecker.correct_teacher(lesson1, teacher_subjects))
        self.assertTrue(ConstraintChecker.correct_teacher(lesson2, teacher_subjects))
        self.assertFalse(ConstraintChecker.correct_teacher(lesson3, teacher_subjects))

    def test_c7_no_room_overlap(self):
        """C7: непересекаемость аудиторий (упрощённый тест)."""
        slot1 = TimeSlot(day=1, start=time(8, 0), end=time(8, 45))
        schedule = {}
        self.assertTrue(ConstraintChecker.no_room_overlap(schedule, None, slot1))


class ScheduleSolverTest(TestCase):
    def test_solver_with_empty_lessons(self):
        solver = ScheduleSolver([])
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 0)
        self.assertEqual(len(unresolved), 0)

    def test_solver_with_single_lesson(self):
        lesson = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        solver = ScheduleSolver([lesson])
        solver.set_teacher_subjects({1: {1}})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 1)
        self.assertEqual(len(unresolved), 0)

    def test_default_slots_count(self):
        slots = ScheduleSolver._default_slots()
        # 6 days × 7 time slots = 42
        self.assertEqual(len(slots), 42)

    def test_solver_multiple_lessons(self):
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=2, class_id=1, teacher_id=1),
            LessonVar(id=3, subject_id=1, class_id=2, teacher_id=2),
            LessonVar(id=4, subject_id=2, class_id=2, teacher_id=2),
        ]
        solver = ScheduleSolver(lessons)
        solver.set_teacher_subjects({1: {1, 2}, 2: {1, 2}})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 4)
        self.assertEqual(len(unresolved), 0)

    def test_solver_no_valid_assignment(self):
        """All lessons have the same teacher & time, should generate some."""
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=1),
            LessonVar(id=3, subject_id=1, class_id=3, teacher_id=1),
        ]
        solver = ScheduleSolver(lessons)
        solver.set_teacher_subjects({1: {1}})
        # Teacher 1 has 3 lessons, each subject 1, each on different classes
        # Should be assignable to different time slots
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 3)
        self.assertEqual(len(unresolved), 0)

    def test_solver_max_hours_constructor(self):
        """max_hours is accepted by constructor and does not crash."""
        lessons = [LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)]
        solver = ScheduleSolver(lessons, max_hours=2)
        solver.set_teacher_subjects({1: {1}})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 1)

    def test_solver_c4_rejects_wrong_subject(self):
        """C4 must be enforced during solve(), not just available as a helper."""
        lesson = LessonVar(id=1, subject_id=99, class_id=1, teacher_id=1)
        solver = ScheduleSolver([lesson])
        solver.set_teacher_subjects({1: {1, 2}})  # teacher 1 cannot teach subject 99
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 0)
        self.assertEqual(len(unresolved), 1)
        self.assertIn('дисциплину', unresolved[0]['reasons'][0])

    def test_solver_c5_respects_per_teacher_workload(self):
        """C5 must be enforced during solve() using a per-teacher max_hours map."""
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=1),
        ]
        # 0.75h per lesson; cap of 1h allows only one of the two lessons.
        solver = ScheduleSolver(lessons, max_hours={1: 1})
        solver.set_teacher_subjects({1: {1}})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 1)
        self.assertEqual(len(unresolved), 1)

    def test_solver_c7_blocks_shared_room_different_classes(self):
        """C7: two different classes sharing a default room cannot overlap."""
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=2),
        ]
        # Only one time slot available forces both lessons into the same slot.
        one_slot = [ScheduleSolver._default_slots()[0]]
        solver = ScheduleSolver(lessons, slots=one_slot)
        solver.set_teacher_subjects({1: {1}, 2: {1}})
        solver.set_class_rooms({1: 'Каб. 101', 2: 'Каб. 101'})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 1)
        self.assertEqual(len(unresolved), 1)

    def test_solver_c7_allows_different_rooms_same_slot(self):
        """C7 must not block classes that use different rooms."""
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=2),
        ]
        one_slot = [ScheduleSolver._default_slots()[0]]
        solver = ScheduleSolver(lessons, slots=one_slot)
        solver.set_teacher_subjects({1: {1}, 2: {1}})
        solver.set_class_rooms({1: 'Каб. 101', 2: 'Каб. 202'})
        solved, unresolved = solver.solve()
        self.assertEqual(len(solved), 2)
        self.assertEqual(len(unresolved), 0)

    def test_solver_incremental_preserves_preassigned(self):
        """Incremental mode must not re-emit already-existing lessons and must
        avoid conflicting with them."""
        existing_slot = ScheduleSolver._default_slots()[0]
        preassigned = {
            'existing_1': {
                'teacher_id': 1, 'class_id': 1,
                'day': existing_slot.day, 'start': existing_slot.start, 'end': existing_slot.end,
            }
        }
        new_lesson = LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1)
        solver = ScheduleSolver([new_lesson])
        solver.set_teacher_subjects({1: {1}})
        solved, unresolved = solver.solve(preassigned=preassigned)
        self.assertEqual(len(solved), 1)
        self.assertNotIn('existing_1', solved)
        # The new lesson for the same teacher/class must not land in the occupied slot.
        placed = list(solved.values())[0]
        self.assertFalse(
            placed['day'] == existing_slot.day and placed['start'] == existing_slot.start
        )


class VariableSelectorTest(TestCase):
    def test_mcv_selects_most_constrained(self):
        """MCV picks the lesson with fewest remaining valid slots."""
        teacher_subjects = {1: {1, 2}, 2: {1}}
        slots = [
            TimeSlot(day=1, start=time(8, 0), end=time(8, 45)),
            TimeSlot(day=1, start=time(8, 55), end=time(9, 40)),
        ]
        constraints = [
            ConstraintChecker.no_teacher_overlap,
            ConstraintChecker.no_class_overlap,
            ConstraintChecker.valid_time,
        ]
        # Pre-assign slot 1 to another lesson with teacher 1
        schedule = {
            99: {
                'teacher_id': 1, 'class_id': 99, 'day': 1,
                'start': time(8, 0), 'end': time(8, 45),
            }
        }
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=2),
        ]
        selected = VariableSelector.select(schedule, lessons, slots, constraints, teacher_subjects, 36)
        self.assertIsNotNone(selected)
        # Teacher 1 already occupies slot 1, so lesson 1 has only 1 valid slot → MCV picks it
        self.assertEqual(selected.teacher_id, 1)


class ValueSelectorTest(TestCase):
    def test_lcv_orders_by_least_constraining(self):
        lessons = [
            LessonVar(id=1, subject_id=1, class_id=1, teacher_id=1),
            LessonVar(id=2, subject_id=1, class_id=2, teacher_id=1),
        ]
        slots = [
            TimeSlot(day=1, start=time(8, 0), end=time(8, 45)),
            TimeSlot(day=1, start=time(8, 55), end=time(9, 40)),
            TimeSlot(day=2, start=time(8, 0), end=time(8, 45)),
        ]
        constraints = [
            ConstraintChecker.no_teacher_overlap,
            ConstraintChecker.no_class_overlap,
            ConstraintChecker.valid_time,
        ]
        ordered = ValueSelector.order({}, lessons[0], slots, lessons, constraints)
        self.assertEqual(len(ordered), 3)


class ScheduleMoveViewTest(TestCase):
    Lesson = None

    def setUp(self):
        from django.test import Client
        from accounts.models import User
        from school.models import Class, Subject
        from schedule.models import Lesson

        ScheduleMoveViewTest.Lesson = Lesson

        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Админ', phone='+0', role='admin',
        )
        self.teacher1 = User.objects.create_user(
            username='t1', password='pass123',
            full_name='Учитель 1', phone='+1', role='teacher',
        )
        self.teacher2 = User.objects.create_user(
            username='t2', password='pass123',
            full_name='Учитель 2', phone='+2', role='teacher',
        )
        self.cls = Class.objects.create(name='10А', default_classroom='Каб. 301')
        self.subj = Subject.objects.create(name='Математика')

        self.lesson = Lesson.objects.create(
            subject=self.subj, teacher=self.teacher1,
            class_group=self.cls, day_of_week=1,
            start_time='08:00', end_time='08:45',
        )

    def _move(self, lesson_id, day, slot):
        self.client.login(username='admin', password='pass123')
        import json
        return self.client.post('/admin/schedule/move/', json.dumps({
            'lesson_id': lesson_id, 'day': day, 'slot': slot,
        }), content_type='application/json')

    def test_move_success(self):
        resp = self._move(self.lesson.id, 2, '08:55–09:40')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.day_of_week, 2)
        self.assertEqual(str(self.lesson.start_time), '08:55:00')

    def test_move_teacher_conflict(self):
        self.Lesson.objects.create(
            subject=self.subj, teacher=self.teacher1,
            class_group=self.cls, day_of_week=2,
            start_time='08:55', end_time='09:40',
        )
        resp = self._move(self.lesson.id, 2, '08:55–09:40')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data['ok'])
        self.assertIn('Преподаватель', data['error'])

    def test_move_class_conflict(self):
        self.Lesson.objects.create(
            subject=self.subj, teacher=self.teacher2,
            class_group=self.cls, day_of_week=2,
            start_time='08:55', end_time='09:40',
        )
        resp = self._move(self.lesson.id, 2, '08:55–09:40')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data['ok'])
        self.assertIn('Класс', data['error'])

    def test_move_invalid_slot(self):
        resp = self._move(self.lesson.id, 2, 'invalid')
        self.assertEqual(resp.status_code, 400)

    def test_move_requires_admin(self):
        self.client.login(username='t1', password='pass123')
        import json
        resp = self.client.post('/admin/schedule/move/', json.dumps({
            'lesson_id': self.lesson.id, 'day': 2, 'slot': '08:55–09:40',
        }), content_type='application/json')
        self.assertEqual(resp.status_code, 302)

    def test_move_no_adjacent_conflict(self):
        """Adjacent time slots should NOT conflict."""
        self.Lesson.objects.create(
            subject=self.subj, teacher=self.teacher1,
            class_group=self.cls, day_of_week=2,
            start_time='08:00', end_time='08:45',
        )
        resp = self._move(self.lesson.id, 2, '08:55–09:40')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])


class ScheduleGenerateViewTest(TestCase):
    """SCH_01: генерация должна работать с чистого листа, если у
    преподавателей явно указаны дисциплины (User.subjects), а не только
    когда в базе уже есть занятия, из которых можно их вывести."""

    def setUp(self):
        from accounts.models import User
        from school.models import Class, ClassSubject, Subject

        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin', password='pass123',
            full_name='Админ', phone='+0', role='admin',
        )
        self.teacher = User.objects.create_user(
            username='t1', password='pass123',
            full_name='Учитель', phone='+1', role='teacher',
            max_hours_per_week=36,
        )
        self.cls = Class.objects.create(name='5А', default_classroom='Каб. 1')
        self.subject = Subject.objects.create(name='Математика')
        ClassSubject.objects.create(class_group=self.cls, subject=self.subject, hours_per_week=3)
        self.ClassSubject = ClassSubject

    def test_cold_start_generation_uses_explicit_teacher_subjects(self):
        """No pre-existing lessons at all — only User.subjects declares who
        can teach what. Previously this produced 0 lessons (bootstrap bug)."""
        self.teacher.subjects.add(self.subject)
        self.client.login(username='admin', password='pass123')
        response = self.client.post(reverse('schedule_generate'), {'mode': 'full'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['created'], 3)

    def test_cold_start_without_subjects_skips_teacher(self):
        """Without an explicit subject assignment, no teacher qualifies for
        the curriculum entry, and the admin gets a clear error naming the
        subject — instead of silently producing zero lessons."""
        self.client.login(username='admin', password='pass123')
        response = self.client.post(reverse('schedule_generate'), {'mode': 'full'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Математика', response.context['error'])
