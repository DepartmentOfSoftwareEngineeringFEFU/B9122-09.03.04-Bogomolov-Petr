"""FR_T2: подача заявки на замену преподавателем через Telegram-бота.

Пошаговый сценарий без ConversationHandler (по аналогии с потоком
выставления оценок в teacher.py): выбор своего урока -> выбор
замещающего преподавателя -> свободный текст с причиной.
"""
from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClient
from bot.keyboards import back_menu, sub_lessons_kb, sub_teachers_kb, teacher_menu

api = ApiClient()


async def substitution_request_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    context.user_data['sub_step'] = None
    context.user_data['sub_data'] = {}

    resp = api.get_lessons(params={'teacher': user_id})
    if resp.status_code != 200:
        text = 'Ошибка получения расписания.'
        if query:
            await query.edit_message_text(text, reply_markup=teacher_menu())
        else:
            await update.message.reply_text(text, reply_markup=teacher_menu())
        return

    results = resp.json().get('results', [])
    if not results:
        text = 'У вас нет занятий в расписании.'
        if query:
            await query.edit_message_text(text, reply_markup=teacher_menu())
        else:
            await update.message.reply_text(text, reply_markup=teacher_menu())
        return

    context.user_data['sub_lessons'] = results
    text = '<b>Шаг 1 из 3:</b> Выберите урок, который нужно заменить:'
    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=sub_lessons_kb(results))
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=sub_lessons_kb(results))


async def substitution_select_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lesson_id = int(query.data.replace('sub_lesson_', ''))
    lessons = context.user_data.get('sub_lessons', [])
    lesson = next((l for l in lessons if l['id'] == lesson_id), None)
    if not lesson:
        await query.edit_message_text('Урок не найден.', reply_markup=teacher_menu())
        return

    context.user_data['sub_data'] = {
        'lesson_id': lesson['id'],
        'lesson_info': (
            f'{lesson.get("subject_name", "?")} ({lesson.get("class_name", "?")}), '
            f'{lesson.get("day_of_week_display", "?")} '
            f'{lesson.get("start_time", "?")}-{lesson.get("end_time", "?")}'
        ),
    }

    user_id = context.user_data.get('user_id')
    resp = api.get_teachers()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения списка преподавателей.', reply_markup=teacher_menu())
        return

    teachers = [t for t in resp.json().get('results', []) if t['id'] != user_id]
    if not teachers:
        await query.edit_message_text('Нет других преподавателей для замены.', reply_markup=teacher_menu())
        return

    context.user_data['sub_teachers'] = teachers
    await query.edit_message_text(
        f'<b>Шаг 2 из 3:</b> Урок: {context.user_data["sub_data"]["lesson_info"]}\n\n'
        f'Кто проведёт замену?',
        parse_mode='HTML',
        reply_markup=sub_teachers_kb(teachers),
    )


async def substitution_select_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    teacher_id = int(query.data.replace('sub_teacher_', ''))
    teachers = context.user_data.get('sub_teachers', [])
    teacher = next((t for t in teachers if t['id'] == teacher_id), None)
    if not teacher:
        await query.edit_message_text('Преподаватель не найден.', reply_markup=teacher_menu())
        return

    context.user_data['sub_data']['new_teacher_id'] = teacher_id
    context.user_data['sub_data']['new_teacher_name'] = teacher['full_name']
    context.user_data['sub_step'] = 'awaiting_reason'

    await query.edit_message_text(
        f'<b>Шаг 3 из 3:</b> {context.user_data["sub_data"]["lesson_info"]}\n'
        f'Замещает: <b>{teacher["full_name"]}</b>\n\n'
        f'Напишите причину замены одним сообщением:',
        parse_mode='HTML',
    )


async def substitution_reason_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MessageHandler для свободного текста — срабатывает только если бот
    ожидает причину замены (sub_step == 'awaiting_reason')."""
    if context.user_data.get('sub_step') != 'awaiting_reason':
        return

    reason = update.message.text.strip()
    data = context.user_data.get('sub_data', {})
    user_id = context.user_data.get('user_id')

    if not reason or not data.get('lesson_id') or not data.get('new_teacher_id') or not user_id:
        await update.message.reply_text('Не удалось отправить заявку. Попробуйте ещё раз через /start.',
                                         reply_markup=teacher_menu())
        context.user_data['sub_step'] = None
        return

    resp = api.create_substitution(
        lesson_id=data['lesson_id'],
        new_teacher_id=data['new_teacher_id'],
        reason=reason,
        initiator_id=user_id,
    )

    context.user_data['sub_step'] = None

    if resp.status_code == 201:
        text = (
            f'✅ <b>Заявка на замену отправлена!</b>\n\n'
            f'{data["lesson_info"]}\n'
            f'Замещает: {data["new_teacher_name"]}\n'
            f'Причина: {reason}\n\n'
            f'Администратор получит уведомление.'
        )
    else:
        text = '❌ Не удалось отправить заявку. Попробуйте снова.'

    await update.message.reply_text(text, parse_mode='HTML', reply_markup=teacher_menu())
