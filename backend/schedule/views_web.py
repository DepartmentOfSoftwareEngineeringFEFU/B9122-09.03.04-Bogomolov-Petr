import json
from datetime import time

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User
from school.models import Class, Subject
from .forms import LessonForm
from .models import Lesson

DAY_NAMES = [
    (1, 'Понедельник'),
    (2, 'Вторник'),
    (3, 'Среда'),
    (4, 'Четверг'),
    (5, 'Пятница'),
    (6, 'Суббота'),
]

TIME_SLOTS = [
    '08:00–08:45', '08:55–09:40', '09:50–10:35',
    '10:45–11:30', '11:40–12:25', '12:35–13:20', '13:30–14:15',
]

SLOT_TIMES = {
    '08:00–08:45': (time(8, 0), time(8, 45)),
    '08:55–09:40': (time(8, 55), time(9, 40)),
    '09:50–10:35': (time(9, 50), time(10, 35)),
    '10:45–11:30': (time(10, 45), time(11, 30)),
    '11:40–12:25': (time(11, 40), time(12, 25)),
    '12:35–13:20': (time(12, 35), time(13, 20)),
    '13:30–14:15': (time(13, 30), time(14, 15)),
}


def _build_schedule_grid(lessons):
    """Build a 2D grid: time_slots × days → list of lessons."""
    grid = {}
    for slot in TIME_SLOTS:
        grid[slot] = {d: [] for d in range(1, 7)}
    for lesson in lessons:
        slot = f'{lesson.start_time:%H:%M}–{lesson.end_time:%H:%M}'
        if slot in grid:
            grid[slot][lesson.day_of_week].append(lesson)
    return grid


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def schedule_list(request):
    class_id = request.GET.get('class_id')
    lessons_qs = Lesson.objects.select_related('subject', 'teacher', 'class_group')
    if class_id:
        lessons_qs = lessons_qs.filter(class_group_id=class_id)
    lessons = lessons_qs.all()
    grid = _build_schedule_grid(lessons)
    classes = Class.objects.all()
    return render(request, 'admin/schedule.html', {
        'grid': grid,
        'time_slots': TIME_SLOTS,
        'day_names': DAY_NAMES,
        'classes': classes,
        'selected_class_id': int(class_id) if class_id else None,
    })


@login_required
@user_passes_test(lambda u: u.role == 'admin')
@csrf_exempt
@require_POST
def schedule_move(request):
    data = json.loads(request.body)
    lesson_id = data.get('lesson_id')
    day = data.get('day')
    slot_key = data.get('slot')

    if not all([lesson_id, day, slot_key]):
        return JsonResponse({'ok': False, 'error': 'Не все поля заполнены'}, status=400)

    if slot_key not in SLOT_TIMES:
        return JsonResponse({'ok': False, 'error': 'Некорректный временной слот'}, status=400)

    lesson = Lesson.objects.select_related('teacher', 'class_group').get(pk=lesson_id)
    new_start, new_end = SLOT_TIMES[slot_key]

    conflicts = Lesson.objects.exclude(pk=lesson_id).filter(
        day_of_week=day,
        start_time__lt=new_end,
        end_time__gt=new_start,
    )

    # C1: teacher overlap
    if conflicts.filter(teacher=lesson.teacher).exists():
        return JsonResponse({'ok': False, 'error': 'Преподаватель уже занят в это время'})

    # C2: class overlap
    if conflicts.filter(class_group=lesson.class_group).exists():
        return JsonResponse({'ok': False, 'error': 'Класс уже занят в это время'})

    lesson.day_of_week = day
    lesson.start_time = new_start
    lesson.end_time = new_end
    lesson.save(update_fields=['day_of_week', 'start_time', 'end_time'])

    return JsonResponse({
        'ok': True,
        'lesson_id': lesson.id,
        'subject': lesson.subject.name,
        'teacher': lesson.teacher.full_name,
        'class_group': lesson.class_group.name,
        'room': lesson.class_group.default_classroom,
    })


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def schedule_add(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('schedule_list')
    else:
        form = LessonForm()
    return render(request, 'admin/schedule_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def schedule_generate(request):
    from .solver import ScheduleSolver

    teachers = User.objects.filter(role='teacher').prefetch_related('lessons_taught')
    classes = Class.objects.all()
    subjects = Subject.objects.all()

    teacher_subjects = {}
    for t in teachers:
        teacher_subjects[t.id] = set()
        for l in Lesson.objects.filter(teacher=t):
            teacher_subjects[t.id].add(l.subject_id)

    lessons = []
    for cls in classes:
        for subj in subjects:
            for teacher in teachers:
                if subj.id in teacher_subjects.get(teacher.id, set()):
                    from .solver import LessonVar
                    lessons.append(LessonVar(
                        id=len(lessons) + 1,
                        subject_id=subj.id,
                        class_id=cls.id,
                        teacher_id=teacher.id,
                    ))

    solver = ScheduleSolver(lessons)
    solver.set_teacher_subjects(teacher_subjects)
    solved, unresolved = solver.solve()

    Lesson.objects.all().delete()
    Lesson.objects.bulk_create([
        Lesson(
            subject_id=entry['subject_id'],
            teacher_id=entry['teacher_id'],
            class_group_id=entry['class_id'],
            day_of_week=entry['day'],
            start_time=entry['start'],
            end_time=entry['end'],
        )
        for entry in solved.values()
    ])
    created = len(solved)

    return render(request, 'admin/schedule_generate.html', {
        'created': created,
        'unresolved': unresolved,
        'total': len(lessons),
    })


@login_required
def my_schedule(request):
    user = request.user
    if user.role == 'student':
        lessons = Lesson.objects.filter(
            class_group=user.student_class,
        ).select_related('subject', 'teacher')
    elif user.role == 'teacher':
        lessons = Lesson.objects.filter(
            teacher=user,
        ).select_related('subject', 'class_group')
    else:
        lessons = Lesson.objects.select_related('subject', 'teacher', 'class_group').all()

    grid = _build_schedule_grid(lessons)

    template = {
        'teacher': 'teacher/schedule.html',
        'student': 'student/schedule.html',
        'admin': 'admin/schedule.html',
    }.get(user.role, 'admin/schedule.html')

    return render(request, template, {
        'grid': grid,
        'time_slots': TIME_SLOTS,
        'day_names': DAY_NAMES,
    })
