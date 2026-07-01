from telegram import Update
from telegram.ext import ContextTypes

from bot.api_client import ApiClient
from bot.keyboards import (admin_menu, back_menu, reports_kb,
                            substitution_item_kb, substitutions_bottom_kb)

api = ApiClient()


async def admin_substitutions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resp = api.get_substitutions(status='pending')
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения замен.', reply_markup=admin_menu())
        return

    subs = resp.json()
    results = subs.get('results') or subs if isinstance(subs, list) else []

    if not results:
        await query.edit_message_text(
            'Нет ожидающих замен.',
            reply_markup=substitutions_bottom_kb(),
        )
        return

    text = 'Ожидающие подтверждения замены:\n\n'
    for i, sub in enumerate(results[:5], 1):
        lesson_info = sub.get('original_lesson_info', {})
        text += (
            f'<b>#{i}</b> • {sub.get("request_date", "")[:10]}\n'
            f'  {lesson_info.get("subject", "—")}, {lesson_info.get("class", "—")}, {lesson_info.get("time", "—")}\n'
            f'  {lesson_info.get("teacher", "—")} → <b>{sub.get("new_teacher_name", "—")}</b>\n'
            f'  Причина: {sub.get("reason", "—")}\n\n'
        )

    await query.edit_message_text(text, parse_mode='HTML')
    for sub in results[:5]:
        await query.message.reply_text(
            f'<b>#{sub["id"]}</b> — подтвердить или отклонить?',
            parse_mode='HTML',
            reply_markup=substitution_item_kb(sub['id']),
        )
    await query.message.reply_text('Действия:', reply_markup=substitutions_bottom_kb())


async def admin_substitutions_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resp = api.get_substitutions()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения замен.', reply_markup=admin_menu())
        return

    subs = resp.json()
    results = subs.get('results') or subs if isinstance(subs, list) else []

    if not results:
        await query.edit_message_text('Нет замен.', reply_markup=admin_menu())
        return

    text = 'Все замены:\n\n'
    for sub in results[:10]:
        status_emoji = {'pending': '⏳', 'confirmed': '✅', 'rejected': '❌'}
        emoji = status_emoji.get(sub.get('status'), '❓')
        lesson_info = sub.get('original_lesson_info', {})
        text += (
            f'{emoji} <b>#{sub["id"]}</b> ({sub.get("status_display", sub["status"])})\n'
            f'  {lesson_info.get("subject", "—")} — {lesson_info.get("class", "—")}\n'
            f'  {lesson_info.get("teacher", "—")} → {sub.get("new_teacher_name", "—")}\n\n'
        )

    await query.edit_message_text(text, parse_mode='HTML', reply_markup=back_menu())


async def substitution_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_id = query.data.replace('sub_confirm_', '')
    resp = api.confirm_substitution(sub_id)
    if resp.status_code == 200:
        await query.edit_message_text(f'✅ Замена #{sub_id} подтверждена.', reply_markup=back_menu())
    else:
        await query.edit_message_text(f'Ошибка подтверждения замены #{sub_id}.', reply_markup=back_menu())


async def substitution_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_id = query.data.replace('sub_reject_', '')
    resp = api.reject_substitution(sub_id)
    if resp.status_code == 200:
        await query.edit_message_text(f'❌ Замена #{sub_id} отклонена.', reply_markup=back_menu())
    else:
        await query.edit_message_text(f'Ошибка отклонения замены #{sub_id}.', reply_markup=back_menu())


async def admin_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Выберите тип отчёта:',
        reply_markup=reports_kb(),
    )


async def report_workload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resp = api.get_workload_report()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения отчёта.', reply_markup=reports_kb())
        return

    data = resp.json()
    text = '📊 <b>Отчёт: Нагрузка преподавателей</b>\n\n'
    total = 0
    for item in data:
        text += f"{item.get('teacher_name', '—')}: <b>{item.get('total_hours', 0)} ч/нед</b>\n"
        total += item.get('total_hours', 0)
    text += f'\n<b>Итого: {total} ч/нед</b>'

    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reports_kb())


async def report_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resp = api.get_grade_statistics()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения статистики.', reply_markup=reports_kb())
        return

    data = resp.json()
    text = '📊 <b>Отчёт: Успеваемость по предметам</b>\n\n'
    for item in data:
        avg = item.get('avg_grade', 0)
        count = item.get('count', 0)
        text += f"{item.get('subject__name', '—')}: ср. <b>{avg:.2f}</b> ({count} оценок)\n"

    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reports_kb())


async def report_substitutions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resp = api.get_substitutions()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения данных.', reply_markup=reports_kb())
        return

    subs = resp.json()
    results = subs.get('results') or subs if isinstance(subs, list) else []
    total = len(results)
    pending = sum(1 for s in results if s.get('status') == 'pending')
    confirmed = sum(1 for s in results if s.get('status') == 'confirmed')
    rejected = sum(1 for s in results if s.get('status') == 'rejected')

    text = (
        '📊 <b>Отчёт: Замены</b>\n\n'
        f'Всего: <b>{total}</b>\n'
        f'⏳ Ожидает: <b>{pending}</b>\n'
        f'✅ Подтверждено: <b>{confirmed}</b>\n'
        f'❌ Отклонено: <b>{rejected}</b>'
    )
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=reports_kb())


async def report_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Отчёт по посещаемости в разработке.',
        reply_markup=reports_kb(),
    )


async def admin_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        'Управление расписанием доступно в веб-интерфейсе:\n'
        'http://localhost:8000/admin/schedule/',
        reply_markup=admin_menu(),
    )


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    resp = api.get_users()
    if resp.status_code != 200:
        await query.edit_message_text('Ошибка получения пользователей.', reply_markup=admin_menu())
        return

    users = resp.json()
    results = users.get('results') or users if isinstance(users, list) else []
    text = '👥 <b>Пользователи системы:</b>\n\n'
    for u in results[:15]:
        role_emoji = {'admin': '🛡️', 'teacher': '👨‍🏫', 'student': '👨‍🎓'}
        emoji = role_emoji.get(u.get('role'), '👤')
        tg_icon = '📱' if u.get('telegram_id') else ''
        text += f"{emoji} {u['full_name']} (@{u['username']}) {tg_icon}\n"

    if len(results) > 15:
        text += f'\n... и ещё {len(results) - 15} пользователей.'
    text += '\n\nУправление пользователями доступно в веб-интерфейсе.'

    await query.edit_message_text(text, parse_mode='HTML', reply_markup=admin_menu())
