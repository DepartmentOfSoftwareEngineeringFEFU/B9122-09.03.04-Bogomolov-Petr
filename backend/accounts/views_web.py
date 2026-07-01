from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from grades.models import Grade
from schedule.models import Lesson
from school.models import Class
from substitutions.models import Substitution
from .forms import ProfileForm, UserCreateForm
from .models import User


@login_required
def dashboard(request):
    role = request.user.role
    ctx = {}
    if role == 'admin':
        ctx = {
            'total_classes': Class.objects.count(),
            'total_teachers': User.objects.filter(role='teacher').count(),
            'total_students': User.objects.filter(role='student').count(),
            'pending_substitutions': Substitution.objects.filter(status='pending').count(),
            'recent_subs': Substitution.objects.select_related(
                'original_lesson__subject', 'new_teacher'
            ).order_by('-request_date')[:5],
        }
    elif role == 'teacher':
        ctx = {
            'my_lessons_count': Lesson.objects.filter(teacher=request.user).count(),
            'my_pending_subs': Substitution.objects.filter(initiator=request.user, status='pending').count(),
            'my_confirmed_subs': Substitution.objects.filter(initiator=request.user, status='confirmed').count(),
        }
    else:
        ctx = {
            'my_grades_count': Grade.objects.filter(student=request.user).count(),
            'my_lessons_count': Lesson.objects.filter(class_group=request.user.student_class).count(),
        }
    template = {
        'admin': 'admin/dashboard.html',
        'teacher': 'teacher/dashboard.html',
        'student': 'student/dashboard.html',
    }.get(role, 'admin/dashboard.html')
    return render(request, template, ctx)


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def users_list(request):
    users = User.objects.select_related('student_class').all()
    return render(request, 'admin/users.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users_list')
    else:
        form = UserCreateForm()
    return render(request, 'admin/user_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users_list')
    else:
        form = UserCreateForm(instance=user)
    return render(request, 'admin/user_form.html', {'form': form, 'edit': True})


@login_required
def profile_edit(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'profile.html', {'form': form})
