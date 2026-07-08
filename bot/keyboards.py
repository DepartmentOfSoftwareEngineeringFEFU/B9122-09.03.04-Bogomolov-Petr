from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Моё расписание', callback_data='my_schedule')],
        [InlineKeyboardButton('Мои оценки', callback_data='my_grades')],
        [InlineKeyboardButton('Запрос замены', callback_data='substitution_request')],
        [InlineKeyboardButton('Отчёты', callback_data='reports_menu')],
    ])


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Замены', callback_data='admin_substitutions'),
         InlineKeyboardButton('Отчёты', callback_data='admin_reports')],
        [InlineKeyboardButton('Расписание', callback_data='admin_schedule'),
         InlineKeyboardButton('Пользователи', callback_data='admin_users')],
    ])


def teacher_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Выставить оценку', callback_data='teacher_grade')],
        [InlineKeyboardButton('Моё расписание', callback_data='my_schedule')],
        [InlineKeyboardButton('Запрос замены', callback_data='substitution_request')],
    ])


def student_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Моё расписание', callback_data='my_schedule')],
        [InlineKeyboardButton('Мои оценки', callback_data='my_grades')],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Назад', callback_data='back_to_menu')],
    ])


# --- Substitution keyboard (per item) ---
def substitution_item_kb(sub_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f'Подтв. #{sub_id}', callback_data=f'sub_confirm_{sub_id}'),
            InlineKeyboardButton(f'Откл. #{sub_id}', callback_data=f'sub_reject_{sub_id}'),
        ],
    ])


def substitutions_bottom_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Обновить', callback_data='admin_substitutions'),
            InlineKeyboardButton('Все замены', callback_data='admin_substitutions_all'),
        ],
    ])


# --- Reports keyboard ---
def reports_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Нагрузка', callback_data='report_workload'),
         InlineKeyboardButton('Замены', callback_data='report_substitutions')],
        [InlineKeyboardButton('Посещаемость', callback_data='report_attendance'),
         InlineKeyboardButton('Успеваемость', callback_data='report_grades')],
        [InlineKeyboardButton('Назад', callback_data='back_to_menu')],
    ])


# --- Lesson keyboard (teacher grade flow) ---
def lessons_kb(lessons):
    rows = []
    for l in lessons:
        label = (
            f'{l.get("day_of_week_display", "?")} '
            f'{l.get("start_time", "?")}-{l.get("end_time", "?")} — '
            f'{l.get("subject_name", "?")} ({l.get("class_name", "?")})'
        )
        rows.append([InlineKeyboardButton(label, callback_data=f'grade_lesson_{l["id"]}')])
    rows.append([InlineKeyboardButton('Отмена', callback_data='back_to_menu')])
    return InlineKeyboardMarkup(rows)


# --- Substitution request flow (teacher) ---
def sub_lessons_kb(lessons):
    rows = []
    for l in lessons:
        label = (
            f'{l.get("day_of_week_display", "?")} '
            f'{l.get("start_time", "?")}-{l.get("end_time", "?")} — '
            f'{l.get("subject_name", "?")} ({l.get("class_name", "?")})'
        )
        rows.append([InlineKeyboardButton(label, callback_data=f'sub_lesson_{l["id"]}')])
    rows.append([InlineKeyboardButton('Отмена', callback_data='back_to_menu')])
    return InlineKeyboardMarkup(rows)


def sub_teachers_kb(teachers):
    rows = []
    for t in teachers:
        rows.append([InlineKeyboardButton(t['full_name'], callback_data=f'sub_teacher_{t["id"]}')])
    rows.append([InlineKeyboardButton('Отмена', callback_data='back_to_menu')])
    return InlineKeyboardMarkup(rows)


# --- Grade flow keyboards ---
def classes_kb(classes):
    rows = []
    row = []
    for c in classes:
        row.append(InlineKeyboardButton(c['name'], callback_data=f'grade_class_{c["id"]}'))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton('Отмена', callback_data='back_to_menu')])
    return InlineKeyboardMarkup(rows)


def subjects_kb(subjects):
    rows = []
    for s in subjects:
        rows.append([InlineKeyboardButton(s['name'], callback_data=f'grade_subject_{s["id"]}')])
    rows.append([InlineKeyboardButton('Назад', callback_data='teacher_grade')])
    return InlineKeyboardMarkup(rows)


def students_kb(students):
    rows = []
    for s in students:
        label = f'{s["full_name"]}'
        rows.append([InlineKeyboardButton(label, callback_data=f'grade_student_{s["id"]}')])
    rows.append([InlineKeyboardButton('Назад', callback_data='grade_back_lessons')])
    return InlineKeyboardMarkup(rows)


def grade_value_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('1', callback_data='grade_val_1'),
         InlineKeyboardButton('2', callback_data='grade_val_2'),
         InlineKeyboardButton('3', callback_data='grade_val_3'),
         InlineKeyboardButton('4', callback_data='grade_val_4'),
         InlineKeyboardButton('5', callback_data='grade_val_5')],
        [InlineKeyboardButton('Отмена', callback_data='back_to_menu')],
    ])


def grade_result_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('Да, далее', callback_data='teacher_grade'),
         InlineKeyboardButton('Завершить', callback_data='back_to_menu')],
    ])
