from collections import Counter

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count
from django.shortcuts import render

from grades.models import Grade
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

    return render(request, 'admin/reports.html', {
        'workload': workload,
        'grade_stats': grade_stats,
        'total_lessons': total_lessons,
        'by_day': dict(by_day),
    })
