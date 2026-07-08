from collections import Counter

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from grades.models import Attendance, Grade
from schedule.models import Lesson


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def reports_dashboard(request):
    workload = (
        Lesson.objects.values('teacher__full_name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    grade_stats = (
        Grade.objects.values('subject__name')
        .annotate(avg_grade=Avg('grade'), count=Count('id'))
        .order_by('subject__name')
    )

    total_lessons = Lesson.objects.count()
    by_day = Counter(Lesson.objects.values_list('day_of_week', flat=True))

    attendance_stats = (
        Attendance.objects.values('lesson__class_group__name')
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
        'workload': workload,
        'grade_stats': grade_stats,
        'total_lessons': total_lessons,
        'by_day': dict(by_day),
        'attendance_stats': attendance_stats,
    })
