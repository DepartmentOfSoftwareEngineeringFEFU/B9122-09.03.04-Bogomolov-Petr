from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClient
from bot.keyboards import (back_menu, grade_result_kb, grade_value_kb,
                            lessons_kb, students_kb, teacher_menu)

api = ApiClient()


async def teacher_grade_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    user_id = context.user_data.get('user_id')
    if not user_id:
        text = 'Сначала выполните вход через /start.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    context.user_data['grade_step'] = 1
    context.user_data['grade_data'] = {}

    resp = api.get_lessons(params={'teacher': user_id})
    if resp.status_code != 200:
        text = 'Ошибка получения расписания.'
        if query:
            await query.edit_message_text(text, reply_markup=teacher_menu())
        else:
            await update.message.reply_text(text, reply_markup=teacher_menu())
        return

    lessons_data = resp.json()
    results = lessons_data.get('results', [])
    if not results:
        text = 'У вас нет занятий в расписании.'
        if query:
            await query.edit_message_text(text, reply_markup=teacher_menu())
        else:
            await update.message.reply_text(text, reply_markup=teacher_menu())
        return

    context.user_data['grade_lessons'] = results

    text = (
        '<b>Шаг 1 из 3:</b> Выберите урок\n\n'
        'Выберите урок из вашего расписания, '
        'в который хотите выставить оценку:'
    )
    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=lessons_kb(results))
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=lessons_kb(results))


async def grade_select_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lesson_id = int(query.data.replace('grade_lesson_', ''))
    lessons = context.user_data.get('grade_lessons', [])

    lesson = None
    for l in lessons:
        if l['id'] == lesson_id:
            lesson = l
            break

    if not lesson:
        await query.edit_message_text('Урок не найден.', reply_markup=teacher_menu())
        return

    context.user_data['grade_step'] = 2
    context.user_data['grade_data'] = {
        'lesson_id': lesson['id'],
        'class_id': lesson['class_group'],
        'class_name': lesson['class_name'],
        'subject_id': lesson['subject'],
        'subject_name': lesson['subject_name'],
        'lesson_info': (
            f'{lesson.get("day_of_week_display", "?")} '
            f'{lesson.get("start_time", "?")}-{lesson.get("end_time", "?")} '
            f'{lesson.get("subject_name", "?")} ({lesson.get("class_name", "?")})'
        ),
    }

    resp = api.get_students_by_class(lesson['class_group'])
    if resp.status_code != 200:
        await query.edit_message_text(
            'Ошибка получения списка учеников.', reply_markup=teacher_menu()
        )
        return

    students_data = resp.json()
    results = students_data.get('results', [])
    context.user_data['grade_students'] = results

    if not results:
        await query.edit_message_text('В этом классе нет учеников.', reply_markup=teacher_menu())
        return

    await query.edit_message_text(
        f'<b>Шаг 2 из 3:</b> Выберите ученика\n\n'
        f'Урок: <b>{lesson["subject_name"]}</b> ({lesson["class_name"]})\n'
        f'{lesson.get("day_of_week_display", "?")} '
        f'{lesson.get("start_time", "?")}-{lesson.get("end_time", "?")}\n\n'
        f'Ученики:',
        parse_mode='HTML',
        reply_markup=students_kb(results),
    )


async def grade_select_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    student_id = int(query.data.replace('grade_student_', ''))
    context.user_data['grade_step'] = 3
    context.user_data['grade_data']['student_id'] = student_id

    students = context.user_data.get('grade_students', [])
    student_name = ''
    for s in students:
        if s['id'] == student_id:
            student_name = s['full_name']
            break
    context.user_data['grade_data']['student_name'] = student_name

    lesson_info = context.user_data['grade_data'].get('lesson_info', '')

    await query.edit_message_text(
        f'<b>Шаг 3 из 3:</b> Оценка для <b>{student_name}</b>\n\n'
        f'{lesson_info}\n\n'
        f'Выберите оценку (1–5):',
        parse_mode='HTML',
        reply_markup=grade_value_kb(),
    )


async def grade_set_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    grade_val = int(query.data.replace('grade_val_', ''))
    context.user_data['grade_data']['grade'] = grade_val

    data = context.user_data['grade_data']
    resp = api.create_grade(
        student_id=data['student_id'],
        subject_id=data['subject_id'],
        grade=grade_val,
        date=date.today().isoformat(),
    )

    if resp.status_code == 201:
        text = (
            f'✅ <b>Оценка выставлена!</b>\n\n'
            f'<b>{data.get("student_name", "")}</b> — '
            f'<b>{data.get("subject_name", "")}</b> — '
            f'<b>{grade_val}</b>\n\n'
            f'Продолжить выставление?'
        )
        reply_markup = grade_result_kb()
    else:
        text = f'❌ Ошибка при выставлении оценки. Попробуйте снова.'
        reply_markup = teacher_menu()

    context.user_data['grade_step'] = 0
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def grade_back_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['grade_step'] = 1
    await teacher_grade_start(update, context)
