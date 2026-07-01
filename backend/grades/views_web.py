from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from accounts.models import User
from grades.models import Grade
from school.models import Class, Subject


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def teacher_grades(request):
    teacher = request.user
    grades = Grade.objects.filter(
        teacher=teacher,
    ).select_related('student', 'subject')
    classes = Class.objects.all()
    return render(request, 'teacher/grades.html', {
        'grades': grades,
        'classes': classes,
    })


@login_required
@user_passes_test(lambda u: u.role == 'teacher')
def grade_add(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        subject_id = request.POST.get('subject')
        grade_val = request.POST.get('grade')
        grade_date = request.POST.get('date')
        if student_id and subject_id and grade_val:
            Grade.objects.create(
                student_id=student_id,
                subject_id=subject_id,
                grade=int(grade_val),
                teacher=request.user,
                date=grade_date or date.today(),
            )
        return redirect('teacher_grades')
    students = User.objects.filter(role='student')
    subjects = Subject.objects.all()
    return render(request, 'teacher/grade_form.html', {
        'students': students,
        'subjects': subjects,
        'today': date.today(),
    })


@login_required
@user_passes_test(lambda u: u.role == 'student')
def student_grades(request):
    from django.db.models import Avg
    grades = Grade.objects.filter(
        student=request.user,
    ).select_related('subject', 'teacher')

    subjects_data = {}
    for g in grades:
        if g.subject not in subjects_data:
            subjects_data[g.subject] = {'grades': [], 'avg': 0}
        subjects_data[g.subject]['grades'].append(g)
    # Compute averages
    for subj, data in subjects_data.items():
        vals = [g.grade for g in data['grades']]
        data['avg'] = sum(vals) / len(vals) if vals else 0

    return render(request, 'student/grades.html', {
        'subjects_data': subjects_data,
    })
