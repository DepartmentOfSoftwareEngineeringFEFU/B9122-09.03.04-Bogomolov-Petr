import json
from collections import Counter
from datetime import time

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User
from school.models import Class, ClassSubject, Subject
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
    if request.method != 'POST':
        return render(request, 'admin/schedule_generate.html', {'created': None})

    from .solver import ScheduleSolver, LessonVar

    mode = request.POST.get('mode', 'full')  # 'full' — с нуля, 'incremental' — дозаполнение

    teachers = list(User.objects.filter(role='teacher').prefetch_related('subjects'))
    teacher_subjects = {}
    teacher_load = {}
    for t in teachers:
        teacher_subjects[t.id] = {s.id for s in t.subjects.all()}
        teacher_load[t.id] = Lesson.objects.filter(teacher=t).count()

    max_hours = {t.id: (t.max_hours_per_week or 36) for t in teachers}
    class_rooms = dict(Class.objects.values_list('id', 'default_classroom'))

    curriculum = ClassSubject.objects.select_related('class_group', 'subject').all()
    if not curriculum.exists():
        return render(request, 'admin/schedule_generate.html', {
            'error': 'Не заполнен учебный план. Добавьте дисциплины для классов.',
            'created': 0, 'unresolved': [], 'total': 0,
        })

    existing_lessons = list(
        Lesson.objects.select_related('subject', 'teacher', 'class_group').all()
    )
    existing_count = Counter((l.class_group_id, l.subject_id) for l in existing_lessons)

    lessons = []
    skipped_no_teacher = []
    next_id = 1
    for entry in curriculum:
        qualified = [t for t in teachers if entry.subject_id in teacher_subjects.get(t.id, set())]
        if not qualified:
            skipped_no_teacher.append(f'{entry.subject.name} ({entry.class_group.name})')
            continue
        # C5/загрузка: выбираем наименее загруженного из квалифицированных преподавателей,
        # чтобы недельная нагрузка (SCH_01) распределялась равномерно.
        teacher = min(qualified, key=lambda t: teacher_load.get(t.id, 0))
        already = existing_count.get((entry.class_group_id, entry.subject_id), 0) if mode == 'incremental' else 0
        need = max(entry.hours_per_week - already, 0)
        for _ in range(need):
            lessons.append(LessonVar(
                id=next_id,
                subject_id=entry.subject_id,
                class_id=entry.class_group_id,
                teacher_id=teacher.id,
            ))
            next_id += 1
        teacher_load[teacher.id] = teacher_load.get(teacher.id, 0) + need

    if not lessons:
        if skipped_no_teacher:
            error = 'Не назначены преподаватели для дисциплин: ' + ', '.join(skipped_no_teacher) + '.'
        elif mode == 'incremental':
            error = 'Расписание уже полностью покрывает учебный план — дозаполнять нечего.'
        else:
            error = 'Нет уроков для генерации. Назначьте преподавателей на дисциплины.'
        return render(request, 'admin/schedule_generate.html', {
            'error': error, 'created': 0, 'unresolved': [], 'total': 0,
        })

    solver = ScheduleSolver(lessons, max_hours=max_hours)
    solver.set_teacher_subjects(teacher_subjects)
    solver.set_class_rooms(class_rooms)

    preassigned = {}
    if mode == 'incremental':
        for l in existing_lessons:
            preassigned[f'existing_{l.id}'] = {
                'teacher_id': l.teacher_id,
                'class_id': l.class_group_id,
                'day': l.day_of_week,
                'start': l.start_time,
                'end': l.end_time,
            }

    solved, unresolved = solver.solve(preassigned=preassigned)

    if mode == 'full':
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

    subjects_map = dict(Subject.objects.values_list('id', 'name'))
    classes_map = dict(Class.objects.values_list('id', 'name'))
    teachers_map = {t.id: t.full_name for t in teachers}

    unresolved_details = [
        {
            'subject': subjects_map.get(item['lesson'].subject_id, '—'),
            'class_name': classes_map.get(item['lesson'].class_id, '—'),
            'teacher': teachers_map.get(item['lesson'].teacher_id, '—'),
            'reasons': item['reasons'],
        }
        for item in unresolved
    ]

    return render(request, 'admin/schedule_generate.html', {
        'created': created,
        'unresolved': unresolved_details,
        'total': len(lessons),
        'mode': mode,
        'skipped_no_teacher': skipped_no_teacher,
    })


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_workload(request):
    user = request.user
    lessons = Lesson.objects.filter(teacher=user).select_related('subject', 'class_group')
    total_hours = sum(
        (l.end_time.hour + l.end_time.minute / 60) - (l.start_time.hour + l.start_time.minute / 60)
        for l in lessons
    )
    max_hours = user.max_hours_per_week or 36
    return render(request, 'teacher/workload.html', {
        'lessons': lessons,
        'total_hours': round(total_hours, 1),
        'max_hours': max_hours,
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
