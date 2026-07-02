from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClassForm, SubjectForm
from .models import Class, ClassSubject, Subject


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


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def curriculum_list(request, class_pk):
    cls = get_object_or_404(Class, pk=class_pk)
    items = ClassSubject.objects.filter(class_group=cls).select_related('subject')
    return render(request, 'admin/curriculum_list.html', {'cls': cls, 'items': items})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def curriculum_add(request, class_pk):
    cls = get_object_or_404(Class, pk=class_pk)
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        hours = request.POST.get('hours_per_week', 2)
        if subject_id:
            ClassSubject.objects.get_or_create(
                class_group=cls,
                subject_id=subject_id,
                defaults={'hours_per_week': hours},
            )
            messages.success(request, 'Дисциплина добавлена в учебный план')
        return redirect('curriculum_list', class_pk=cls.pk)
    subjects = Subject.objects.exclude(
        id__in=ClassSubject.objects.filter(class_group=cls).values('subject_id')
    )
    return render(request, 'admin/curriculum_form.html', {'cls': cls, 'subjects': subjects})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def curriculum_edit(request, pk):
    item = get_object_or_404(ClassSubject, pk=pk)
    if request.method == 'POST':
        hours = request.POST.get('hours_per_week', 2)
        try:
            item.hours_per_week = int(hours)
            item.save(update_fields=['hours_per_week'])
            messages.success(request, 'Учебный план обновлён')
        except (ValueError, TypeError):
            messages.error(request, 'Некорректное количество часов')
        return redirect('curriculum_list', class_pk=item.class_group_id)
    return render(request, 'admin/curriculum_edit.html', {'item': item})


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def curriculum_delete(request, pk):
    item = get_object_or_404(ClassSubject, pk=pk)
    class_pk = item.class_group_id
    item.delete()
    messages.success(request, 'Дисциплина удалена из учебного плана')
    return redirect('curriculum_list', class_pk=class_pk)