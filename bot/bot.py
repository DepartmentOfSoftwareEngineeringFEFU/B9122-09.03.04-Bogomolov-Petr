import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.request import HTTPXRequest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')
sys.path.insert(0, str(PROJECT_ROOT))

from bot.handlers.admin import (admin_reports, admin_schedule, admin_users,
                                 admin_substitutions, admin_substitutions_all,
                                 report_attendance, report_grades,
                                 report_substitutions, report_workload,
                                 substitution_confirm, substitution_reject)
from bot.handlers.start import (back_to_menu, my_grades, my_schedule, start,
                                 substitution_request_placeholder)
from bot.handlers.teacher import (grade_back_lessons, grade_select_lesson,
                                    grade_select_student, grade_set_value,
                                    teacher_grade_start)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
PROXY = os.getenv('TELEGRAM_PROXY')


def main():
    request = HTTPXRequest(proxy=PROXY) if PROXY else HTTPXRequest()
    if PROXY:
        print(f'Using proxy: {PROXY}')
    app = Application.builder().token(TOKEN).request(request).build()

    # Basic commands
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('my_schedule', my_schedule))
    app.add_handler(CommandHandler('my_grades', my_grades))
    app.add_handler(CommandHandler('substitutions', admin_substitutions))
    app.add_handler(CommandHandler('reports', admin_reports))
    app.add_handler(CommandHandler('schedule', admin_schedule))
    app.add_handler(CommandHandler('users', admin_users))
    app.add_handler(CommandHandler('grade', teacher_grade_start))

    # Navigation
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))

    # Admin: substitutions
    app.add_handler(CallbackQueryHandler(admin_substitutions, pattern='^admin_substitutions$'))
    app.add_handler(CallbackQueryHandler(admin_substitutions_all, pattern='^admin_substitutions_all$'))
    app.add_handler(CallbackQueryHandler(substitution_confirm, pattern='^sub_confirm_'))
    app.add_handler(CallbackQueryHandler(substitution_reject, pattern='^sub_reject_'))

    # Admin: reports
    app.add_handler(CallbackQueryHandler(admin_reports, pattern='^admin_reports$'))
    app.add_handler(CallbackQueryHandler(report_workload, pattern='^report_workload$'))
    app.add_handler(CallbackQueryHandler(report_grades, pattern='^report_grades$'))
    app.add_handler(CallbackQueryHandler(report_substitutions, pattern='^report_substitutions$'))
    app.add_handler(CallbackQueryHandler(report_attendance, pattern='^report_attendance$'))

    # Admin: schedule / users
    app.add_handler(CallbackQueryHandler(admin_schedule, pattern='^admin_schedule$'))
    app.add_handler(CallbackQueryHandler(admin_users, pattern='^admin_users$'))

    # Teacher: grade flow
    app.add_handler(CallbackQueryHandler(teacher_grade_start, pattern='^teacher_grade$'))
    app.add_handler(CallbackQueryHandler(grade_select_lesson, pattern='^grade_lesson_'))
    app.add_handler(CallbackQueryHandler(grade_select_student, pattern='^grade_student_'))
    app.add_handler(CallbackQueryHandler(grade_set_value, pattern='^grade_val_'))
    app.add_handler(CallbackQueryHandler(grade_back_lessons, pattern='^grade_back_lessons$'))

    # Common
    app.add_handler(CallbackQueryHandler(my_schedule, pattern='^my_schedule$'))
    app.add_handler(CallbackQueryHandler(my_grades, pattern='^my_grades$'))
    app.add_handler(CallbackQueryHandler(substitution_request_placeholder, pattern='^substitution_request$'))

    print('Bot started (polling)...')
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
