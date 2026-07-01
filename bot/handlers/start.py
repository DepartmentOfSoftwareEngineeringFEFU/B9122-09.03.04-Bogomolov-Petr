from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClient
from bot.keyboards import admin_menu, back_menu, main_menu, student_menu, teacher_menu

api = ApiClient()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    context.user_data['telegram_id'] = telegram_id

    user = api.get_user_by_telegram(telegram_id)
    if not user:
        await update.message.reply_text(
            'Добро пожаловать!\n'
            'Это бот системы управления школой.\n\n'
            'Ваш Telegram ID не привязан к учётной записи.\n'
            'Пожалуйста, войдите в веб-интерфейс и привяжите Telegram ID в настройках профиля.\n\n'
            f'Ваш Telegram ID: <code>{telegram_id}</code>',
            parse_mode='HTML',
        )
        return

    context.user_data['user_id'] = user['id']
    context.user_data['role'] = user['role']
    context.user_data['full_name'] = user['full_name']

    role_display = user.get('role_display', user['role'])
    welcome = f'Добро пожаловать, {user["full_name"]}!\nВы вошли как <b>{role_display}</b>.'

    if user['role'] == 'admin':
        welcome += '\n\nДоступные команды:\n/substitutions — просмотр и подтверждение замен\n/reports — формирование отчётов\n/schedule — управление расписанием\n/users — управление пользователями'
        reply_markup = admin_menu()
    elif user['role'] == 'teacher':
        welcome += '\n\nДоступные команды:\n/grade — выставление оценки\n/my_schedule — моё расписание'
        reply_markup = teacher_menu()
    else:
        welcome += '\n\nДоступные команды:\n/my_schedule — моё расписание\n/my_grades — мои оценки'
        reply_markup = student_menu()

    await update.message.reply_text(welcome, parse_mode='HTML', reply_markup=reply_markup)


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    role = context.user_data.get('role', 'student')
    name = context.user_data.get('full_name', 'Пользователь')
    if role == 'admin':
        text = f'Администратор: <b>{name}</b>\nВыберите раздел:'
        reply_markup = admin_menu()
    elif role == 'teacher':
        text = f'Преподаватель: <b>{name}</b>\nВыберите раздел:'
        reply_markup = teacher_menu()
    else:
        text = f'Учащийся: <b>{name}</b>\nВыберите раздел:'
        reply_markup = student_menu()
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def my_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    user_id = context.user_data.get('user_id')
    role = context.user_data.get('role')
    if not user_id:
        text = 'Сначала выполните вход через команду /start.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    resp = api.get_schedule(user_id, role)
    if resp.status_code != 200:
        text = 'Ошибка получения расписания.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    lessons = resp.json()
    results = lessons.get('results', [])
    if not results:
        text = 'У вас нет занятий.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    by_day = {}
    for l in results:
        day = l.get('day_of_week_display', f'День {l.get("day_of_week")}')
        by_day.setdefault(day, []).append(l)

    text = 'Ваше расписание:\n\n'
    days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    for day in days_order:
        if day in by_day:
            text += f'<b>{day}</b>:\n'
            for l in by_day[day]:
                text += f"  — {l.get('subject_name', '—')} ({l.get('start_time')}-{l.get('end_time')}, {l.get('class_name', '')})\n"
            text += '\n'

    user_id_val = context.user_data.get('user_id')
    role_val = context.user_data.get('role')
    if role_val == 'admin':
        reply_markup = admin_menu()
    elif role_val == 'teacher':
        reply_markup = teacher_menu()
    else:
        reply_markup = student_menu()

    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def my_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    user_id = context.user_data.get('user_id')
    role = context.user_data.get('role')
    if not user_id:
        text = 'Сначала выполните вход через команду /start.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    if role == 'teacher':
        text = 'Для выставления оценок используйте /grade или кнопку "Выставить оценку".'
        if query:
            await query.edit_message_text(text, reply_markup=teacher_menu())
        else:
            await update.message.reply_text(text, reply_markup=teacher_menu())
        return

    resp = api.get_grades(user_id)
    if resp.status_code != 200:
        text = 'Ошибка получения оценок.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    grades_data = resp.json()
    results = grades_data.get('results', [])
    if not results:
        text = 'У вас пока нет оценок.'
        if query:
            await query.edit_message_text(text, reply_markup=back_menu())
        else:
            await update.message.reply_text(text, reply_markup=back_menu())
        return

    by_subject = {}
    for g in results:
        subj = g.get('subject_name', '—')
        by_subject.setdefault(subj, []).append(g['grade'])

    text = 'Ваши оценки:\n\n'
    total_sum = 0
    total_count = 0
    for subj, grades in by_subject.items():
        avg = sum(grades) / len(grades)
        total_sum += sum(grades)
        total_count += len(grades)
        text += f"<b>{subj}</b>: {', '.join(str(g) for g in grades)}  (ср. {avg:.1f})\n"

    if total_count:
        text += f'\nОбщий средний балл: <b>{total_sum / total_count:.2f}</b>'

    reply_markup = back_menu()
    if query:
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def substitution_request_placeholder(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Для запроса замены обратитесь к администратору или используйте веб-интерфейс.',
        reply_markup=back_menu(),
    )
