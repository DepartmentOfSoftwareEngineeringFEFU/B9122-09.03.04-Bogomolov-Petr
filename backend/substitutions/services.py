"""Бизнес-логика уведомлений при создании/подтверждении/отклонении замены."""
from accounts.models import User
from accounts.notifications import notify_users, send_telegram_message


def _fmt_time(value):
    """Форматирует время занятия независимо от того, загружено ли значение
    из БД (datetime.time) или это ещё не сохранённый в БД объект (str)."""
    return value.strftime('%H:%M') if hasattr(value, 'strftime') else str(value)[:5]


def notify_substitution_created(sub):
    """TG_06/FR_A6: администратор уведомляется о новом запросе на замену."""
    admins = User.objects.filter(role='admin')
    text = (
        '🔔 <b>Новый запрос на замену</b>\n'
        f'{sub.original_lesson.subject.name} — {sub.original_lesson.class_group.name}\n'
        f'{sub.initiator.full_name} → {sub.new_teacher.full_name}\n'
        f'Причина: {sub.reason}'
    )
    return notify_users(admins, text)


def notify_substitution_result(sub):
    """FR_T5/FR_S3/TG_04: уведомление о статусе замены инициатору,
    новому преподавателю и учащимся затронутого класса."""
    lesson = sub.original_lesson
    if sub.status == sub.Status.CONFIRMED:
        send_telegram_message(
            sub.initiator.telegram_id,
            f'✅ Ваш запрос на замену по «{lesson.subject.name}» ({lesson.class_group.name}) '
            f'подтверждён. Проведёт: {sub.new_teacher.full_name}.',
        )
        send_telegram_message(
            sub.new_teacher.telegram_id,
            f'📌 Вам назначена замена: «{lesson.subject.name}» ({lesson.class_group.name}), '
            f'{lesson.get_day_of_week_display()} {_fmt_time(lesson.start_time)}–{_fmt_time(lesson.end_time)}.',
        )
        students = lesson.class_group.students.all()
        notify_users(
            students,
            f'📢 Уведомление: замена по «{lesson.subject.name}», '
            f'{lesson.get_day_of_week_display()} {_fmt_time(lesson.start_time)}. '
            f'Преподаватель: {sub.new_teacher.full_name} вместо {lesson.teacher.full_name}.',
        )
    else:
        send_telegram_message(
            sub.initiator.telegram_id,
            f'❌ Ваш запрос на замену по «{lesson.subject.name}» ({lesson.class_group.name}) отклонён.',
        )
