from collections import Counter, defaultdict

from django.db.models import Avg, Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAdminUser])
def workload_report(request):
    from django.contrib.auth import get_user_model
    from schedule.models import Lesson

    User = get_user_model()
    teachers = User.objects.filter(role='teacher')
    data = []
    for teacher in teachers:
        lessons = Lesson.objects.filter(teacher=teacher)
        total_hours = sum(
            (l.end_time.hour + l.end_time.minute / 60) - (l.start_time.hour + l.start_time.minute / 60)
            for l in lessons
        )
        data.append({
            'teacher_id': teacher.id,
            'teacher_name': teacher.full_name,
            'lesson_count': lessons.count(),
            'total_hours': round(total_hours, 1),
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def grade_statistics(request):
    from grades.models import Grade

    stats = (
        Grade.objects.values('subject__name')
        .annotate(
            avg_grade=Avg('grade'),
            count=Count('id'),
        )
        .order_by('subject__name')
    )
    return Response(list(stats))


@api_view(['GET'])
@permission_classes([IsAdminUser])
def schedule_summary(request):
    from schedule.models import Lesson

    total = Lesson.objects.count()
    by_day = Counter(Lesson.objects.values_list('day_of_week', flat=True))
    by_type = Counter(Lesson.objects.values_list('lesson_type', flat=True))
    return Response({
        'total_lessons': total,
        'by_day': dict(by_day),
        'by_type': dict(by_type),
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def attendance_report(request):
    """FR_A5/UI_06: сводка по посещаемости — доля присутствий по классам."""
    from grades.models import Attendance

    stats = (
        Attendance.objects.values('lesson__class_group__name')
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(present=True)),
        )
        .order_by('lesson__class_group__name')
    )
    data = [
        {
            'class_name': item['lesson__class_group__name'],
            'total': item['total'],
            'present': item['present'],
            'attendance_rate': round(100 * item['present'] / item['total'], 1) if item['total'] else 0,
        }
        for item in stats
    ]
    return Response(data)
