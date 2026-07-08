from collections import Counter

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from grades.models import Attendance, Grade
from school.models import Class, Subject
from schedule.models import Lesson


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def reports_dashboard(request):
    """FR_A5/UI_06: метрики и графики по успеваемости, посещаемости и
    нагрузке с возможностью фильтрации по классу и предмету."""
    class_id = request.GET.get('class_id') or None
    subject_id = request.GET.get('subject_id') or None

    lessons_qs = Lesson.objects.all()
    if class_id:
        lessons_qs = lessons_qs.filter(class_group_id=class_id)
    if subject_id:
        lessons_qs = lessons_qs.filter(subject_id=subject_id)

    workload = (
        lessons_qs.values('teacher__full_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    grades_qs = Grade.objects.all()
    if class_id:
        grades_qs = grades_qs.filter(student__student_class_id=class_id)
    if subject_id:
        grades_qs = grades_qs.filter(subject_id=subject_id)

    grade_stats = (
        grades_qs.values('subject__name')
        .annotate(avg_grade=Avg('grade'), count=Count('id'))
        .order_by('subject__name')
    )

    grade_trend = (
        grades_qs.values('date')
        .annotate(avg_grade=Avg('grade'))
        .order_by('date')
    )
    grade_trend_labels = [item['date'].strftime('%d.%m.%Y') for item in grade_trend]
    grade_trend_values = [round(item['avg_grade'], 2) for item in grade_trend]

    grade_distribution = {str(v): 0 for v in range(1, 6)}
    for row in grades_qs.values('grade').annotate(count=Count('id')):
        grade_distribution[str(row['grade'])] = row['count']

    total_lessons = lessons_qs.count()
    by_day = Counter(lessons_qs.values_list('day_of_week', flat=True))

    attendance_qs = Attendance.objects.all()
    if class_id:
        attendance_qs = attendance_qs.filter(lesson__class_group_id=class_id)
    if subject_id:
        attendance_qs = attendance_qs.filter(lesson__subject_id=subject_id)

    attendance_stats = (
        attendance_qs.values('lesson__class_group__name')
        .annotate(total=Count('id'), present=Count('id', filter=Q(present=True)))
        .order_by('lesson__class_group__name')
    )
    attendance_stats = [
        {
            'class_name': item['lesson__class_group__name'],
            'total': item['total'],
            'present': item['present'],
            'rate': round(100 * item['present'] / item['total'], 1) if item['total'] else 0,
        }
        for item in attendance_stats
    ]

    return render(request, 'admin/reports.html', {
        'classes': Class.objects.all(),
        'subjects': Subject.objects.all(),
        'selected_class_id': int(class_id) if class_id else None,
        'selected_subject_id': int(subject_id) if subject_id else None,

        'workload': workload,
        'grade_stats': grade_stats,
        'total_lessons': total_lessons,
        'by_day': dict(by_day),
        'attendance_stats': attendance_stats,

        'grade_trend_labels': grade_trend_labels,
        'grade_trend_values': grade_trend_values,
        'grade_distribution_labels': list(grade_distribution.keys()),
        'grade_distribution_values': list(grade_distribution.values()),
        'workload_labels': [w['teacher__full_name'] for w in workload],
        'workload_values': [w['count'] for w in workload],
        'attendance_labels': [a['class_name'] for a in attendance_stats],
        'attendance_values': [a['rate'] for a in attendance_stats],
    })
