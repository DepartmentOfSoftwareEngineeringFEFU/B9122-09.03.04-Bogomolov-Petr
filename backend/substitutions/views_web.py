from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from schedule.models import Lesson
from .models import Substitution


@login_required
def substitutions_list(request):
    if request.user.role == 'admin':
        subs = Substitution.objects.select_related(
            'original_lesson', 'new_teacher', 'initiator',
        ).all()
        return render(request, 'admin/substitutions.html', {'subs': subs})
    else:
        subs = Substitution.objects.filter(
            initiator=request.user,
        ).select_related('original_lesson', 'new_teacher')
        return render(request, 'teacher/substitutions.html', {'subs': subs})


@login_required
def substitution_confirm(request, pk):
    sub = get_object_or_404(Substitution, pk=pk)
    if request.user.role != 'admin':
        messages.error(request, 'Только администратор может подтверждать замены')
        return redirect('substitutions_list')
    sub.status = Substitution.Status.CONFIRMED
    sub.save(update_fields=['status'])
    messages.success(request, 'Замена подтверждена')
    return redirect('substitutions_list')


@login_required
def substitution_reject(request, pk):
    sub = get_object_or_404(Substitution, pk=pk)
    if request.user.role != 'admin':
        messages.error(request, 'Только администратор может отклонять замены')
        return redirect('substitutions_list')
    sub.status = Substitution.Status.REJECTED
    sub.save(update_fields=['status'])
    messages.success(request, 'Замена отклонена')
    return redirect('substitutions_list')


@login_required
def substitution_request(request):
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson')
        new_teacher_id = request.POST.get('new_teacher')
        reason = request.POST.get('reason')
        if lesson_id and new_teacher_id and reason:
            Substitution.objects.create(
                original_lesson_id=lesson_id,
                new_teacher_id=new_teacher_id,
                initiator=request.user,
                reason=reason,
            )
            messages.success(request, 'Запрос на замену отправлен')
            return redirect('substitutions_list')
        messages.error(request, 'Заполните все поля')
    lessons = Lesson.objects.filter(
        teacher=request.user,
    ).select_related('subject', 'class_group')
    from accounts.models import User
    teachers = User.objects.filter(role='teacher').exclude(id=request.user.id)
    return render(request, 'teacher/substitution_request.html', {
        'lessons': lessons,
        'teachers': teachers,
    })