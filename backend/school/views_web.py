from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClassForm, SubjectForm
from .models import Class, Subject


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def classes_list(request):
    classes = Class.objects.select_related('homeroom_teacher').all()
    subjects = Subject.objects.all()
    return render(request, 'admin/classes.html', {'classes': classes, 'subjects': subjects})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def class_create(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Класс успешно создан')
            return redirect('classes_list')
    else:
        form = ClassForm()
    return render(request, 'admin/class_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def class_edit(request, pk):
    cls = get_object_or_404(Class, pk=pk)
    if request.method == 'POST':
        form = ClassForm(request.POST, instance=cls)
        if form.is_valid():
            form.save()
            messages.success(request, 'Класс успешно обновлён')
            return redirect('classes_list')
    else:
        form = ClassForm(instance=cls)
    return render(request, 'admin/class_form.html', {'form': form, 'edit': True})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def subjects_list(request):
    subjects = Subject.objects.all()
    return render(request, 'admin/subjects.html', {'subjects': subjects})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дисциплина успешно создана')
            return redirect('subjects_list')
    else:
        form = SubjectForm()
    return render(request, 'admin/subject_form.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Дисциплина успешно обновлена')
            return redirect('subjects_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'admin/subject_form.html', {'form': form, 'edit': True})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Дисциплина удалена')
        return redirect('subjects_list')
    return render(request, 'admin/subject_confirm_delete.html', {'subject': subject})