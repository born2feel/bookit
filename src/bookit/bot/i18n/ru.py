MESSAGES: dict[str, str] = {
    # --- форматирование ---
    "weekday.0": "пн",
    "weekday.1": "вт",
    "weekday.2": "ср",
    "weekday.3": "чт",
    "weekday.4": "пт",
    "weekday.5": "сб",
    "weekday.6": "вс",
    "fmt.datetime": "{day} в {time}",
    "fmt.minutes": "{n} мин",
    # --- команды ---
    "cmd.start": "Главное меню",
    "cmd.help": "Справка",
    "cmd.cancel": "Отменить текущее действие",
    "cmd.language": "Сменить язык",
    # --- общее ---
    "menu.welcome": (
        "👋 Добро пожаловать в <b>BookIt</b>!\n\n"
        "Здесь можно записаться на услугу и управлять своими записями."
    ),
    "menu.help": (
        "<b>Как пользоваться ботом</b>\n\n"
        "📅 <b>Записаться</b> — выберите услугу, дату и свободное время.\n"
        "📋 <b>Мои записи</b> — список предстоящих записей, их можно отменить.\n\n"
        "/start — главное меню\n"
        "/language — сменить язык\n"
        "/cancel — прервать текущее действие\n"
        "/help — эта справка"
    ),
    "menu.cancelled": "Действие отменено.",
    "menu.nothing_to_cancel": "Отменять нечего.",
    "menu.unknown_input": "Я не понял сообщение 🤔 Воспользуйтесь кнопками или нажмите /start.",
    "menu.stale_button": "Эта кнопка устарела. Нажмите /start, чтобы начать заново.",
    "language.choose": "Выберите язык / Choose language:",
    "language.changed": "✅ Язык переключён на русский.",
    # --- кнопки ---
    "btn.book": "📅 Записаться",
    "btn.my_bookings": "📋 Мои записи",
    "btn.admin": "⚙️ Админ-панель",
    "btn.language": "🌐 Язык",
    "btn.to_menu": "🏠 В меню",
    "btn.to_main_menu": "🏠 В главное меню",
    "btn.back_to_services": "⬅️ К услугам",
    "btn.back_to_dates": "⬅️ К датам",
    "btn.other_time": "⬅️ Другое время",
    "btn.confirm": "✅ Подтвердить",
    "btn.cancel_booking": "❌ Отменить {when}",
    "btn.yes_cancel": "Да, отменить",
    "btn.no_keep": "Нет, оставить",
    "btn.no": "Нет",
    "btn.admin_services": "🧾 Услуги",
    "btn.admin_bookings": "📅 Записи на дату",
    "btn.admin_days_off": "🌴 Выходные",
    "btn.to_admin": "⬅️ В админ-панель",
    "btn.add_service": "➕ Добавить услугу",
    "btn.edit_price": "💰 Изменить цену",
    "btn.edit_duration": "⏱ Изменить длительность",
    "btn.hide_service": "🙈 Скрыть из каталога",
    "btn.show_service": "👁 Вернуть в каталог",
    "btn.to_services": "⬅️ К услугам",
    "btn.add_day_off": "➕ Добавить выходной",
    "btn.remove_day_off": "🗑 Убрать {day}",
    "btn.to_days_off": "⬅️ К выходным",
    # --- запись клиента ---
    "booking.no_services": "Сейчас нет доступных услуг. Загляните позже 🙏",
    "booking.choose_service": "Выберите услугу:",
    "booking.no_dates": "Свободных дат в ближайшее время нет 😔",
    "booking.choose_date": "Выберите дату:",
    "booking.no_slots": "На {day} свободного времени нет",
    "booking.slots": "Свободное время на {day}:",
    "booking.summary": ("Проверьте запись:\n\n🧾 {service}\n📅 {when}\n⏱ {duration}\n💰 {price}"),
    "booking.created": (
        "✅ Вы записаны!\n\n{booking}\n\nОтменить запись можно в разделе «Мои записи»."
    ),
    "my.empty": "У вас нет предстоящих записей.",
    "my.title": "<b>Ваши записи:</b>",
    "my.ask_cancel": "Отменить запись?\n\n{booking}",
    "my.cancelled": "✅ Запись отменена.",
    # --- услуги ---
    "service.line": "{name} — {duration}, {price}",
    "service.button": "{name} · {duration} · {price}",
    "service.card": ("<b>{name}</b>\nДлительность: {duration}\nЦена: {price}\nСтатус: {status}"),
    "service.status_active": "✅ доступна для записи",
    "service.status_hidden": "🙈 скрыта",
    # --- админ-панель ---
    "admin.menu": "⚙️ <b>Админ-панель</b>",
    "admin.services_title": "<b>Услуги</b>",
    "admin.services_empty": "Услуг пока нет. Добавьте первую!",
    "admin.ask_name": "Введите название услуги (или /cancel для отмены):",
    "admin.ask_duration": "Длительность в минутах, например 60:",
    "admin.ask_price": "Цена в рублях, например 1500:",
    "admin.service_added": "✅ Услуга добавлена",
    "admin.ask_new_price": "Введите новую цену в рублях (или /cancel):",
    "admin.price_updated": "✅ Цена обновлена",
    "admin.ask_new_duration": (
        "Введите новую длительность в минутах (или /cancel).\nУже созданные записи не изменятся."
    ),
    "admin.duration_updated": "✅ Длительность обновлена",
    "admin.choose_date": "Выберите дату, чтобы посмотреть записи:",
    "admin.day_title": "<b>Записи на {day}</b>",
    "admin.day_empty": "На {day} записей нет.",
    "admin.ask_cancel": "Отменить запись? Клиент получит уведомление.\n\n{booking}",
    "admin.booking_cancelled": "✅ Запись отменена.",
    "admin.days_off_title": "<b>Выходные дни</b>",
    "admin.days_off_empty": "Выходных не запланировано.",
    "admin.day_off_removed": "✅ Выходной убран.",
    "admin.ask_day_off": "Введите дату выходного в формате ДД.ММ.ГГГГ (или /cancel):",
    "admin.ask_reason": "Причина (необязательно). Отправьте «{skip}», чтобы пропустить:",
    "admin.day_off_added": "✅ Выходной добавлен.",
    # --- уведомления ---
    "notify.new_booking": "🆕 Новая запись\n{booking}\n👤 {client}",
    "notify.client_cancelled": "↩️ Клиент отменил запись\n{booking}\n👤 {client}",
    "notify.admin_cancelled": (
        "⚠️ Ваша запись отменена администратором:\n{booking}\n\n"
        "Вы можете выбрать другое время через /start."
    ),
    # --- ошибки ---
    "error.generic": "Произошла ошибка",
    "error.unexpected": "Что-то пошло не так 😔 Попробуйте ещё раз или нажмите /start.",
    "error.service_not_found": "Услуга не найдена",
    "error.service_inactive": "Эта услуга сейчас недоступна для записи",
    "error.date_unavailable": "На эту дату записаться нельзя",
    "error.slot_unavailable": "Это время уже занято или недоступно. Выберите другое.",
    "error.booking_not_found": "Запись не найдена или уже отменена",
    "error.booking_already_cancelled": "Запись уже отменена",
    "error.booking_in_past": "Нельзя отменить запись, время которой уже наступило",
    "error.day_off_exists": "Этот день уже отмечен как выходной",
    "error.day_off_not_found": "Выходной не найден",
    "error.day_has_bookings": ("На этот день есть активные записи ({count}). Сначала отмените их."),
    "validation.generic": "Некорректные данные",
    "validation.bad_date": "Некорректная дата",
    "validation.duration_not_int": "Длительность — целое число минут, например 60",
    "validation.duration_range": "Длительность должна быть от {min} до {max} минут",
    "validation.price_not_number": "Цена — число, например 1500 или 1499.90",
    "validation.price_range": "Цена должна быть от 0 до {max}",
    "validation.price_precision": "У цены не может быть больше двух знаков после запятой",
    "validation.name_empty": "Название не может быть пустым",
    "validation.name_too_long": "Название должно быть не длиннее {max} символов",
    "validation.date_format": (
        "Введите существующую дату в формате ДД.ММ.ГГГГ, например 31.12.2026"
    ),
    "validation.day_off_in_past": "Нельзя сделать выходным день в прошлом",
    "validation.reason_too_long": "Причина должна быть не длиннее {max} символов",
}
