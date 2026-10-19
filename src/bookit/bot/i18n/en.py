MESSAGES: dict[str, str] = {
    # --- formatting ---
    "weekday.0": "Mon",
    "weekday.1": "Tue",
    "weekday.2": "Wed",
    "weekday.3": "Thu",
    "weekday.4": "Fri",
    "weekday.5": "Sat",
    "weekday.6": "Sun",
    "fmt.datetime": "{day} at {time}",
    "fmt.minutes": "{n} min",
    # --- commands ---
    "cmd.start": "Main menu",
    "cmd.help": "Help",
    "cmd.cancel": "Cancel current action",
    "cmd.language": "Change language",
    # --- common ---
    "menu.welcome": (
        "👋 Welcome to <b>BookIt</b>!\n\nBook a service and manage your appointments here."
    ),
    "menu.help": (
        "<b>How to use the bot</b>\n\n"
        "📅 <b>Book</b> — choose a service, a date and a free time slot.\n"
        "📋 <b>My bookings</b> — your upcoming appointments; you can cancel them.\n\n"
        "/start — main menu\n"
        "/language — change language\n"
        "/cancel — abort the current action\n"
        "/help — this help"
    ),
    "menu.cancelled": "Action cancelled.",
    "menu.nothing_to_cancel": "Nothing to cancel.",
    "menu.unknown_input": "I didn't understand that 🤔 Please use the buttons or press /start.",
    "menu.stale_button": "This button has expired. Press /start to begin again.",
    "language.choose": "Выберите язык / Choose language:",
    "language.changed": "✅ Language switched to English.",
    # --- buttons ---
    "btn.book": "📅 Book",
    "btn.my_bookings": "📋 My bookings",
    "btn.admin": "⚙️ Admin panel",
    "btn.language": "🌐 Language",
    "btn.to_menu": "🏠 Menu",
    "btn.to_main_menu": "🏠 Main menu",
    "btn.back_to_services": "⬅️ Services",
    "btn.back_to_dates": "⬅️ Dates",
    "btn.other_time": "⬅️ Another time",
    "btn.confirm": "✅ Confirm",
    "btn.cancel_booking": "❌ Cancel {when}",
    "btn.yes_cancel": "Yes, cancel",
    "btn.no_keep": "No, keep it",
    "btn.no": "No",
    "btn.admin_services": "🧾 Services",
    "btn.admin_bookings": "📅 Bookings by date",
    "btn.admin_days_off": "🌴 Days off",
    "btn.to_admin": "⬅️ Admin panel",
    "btn.add_service": "➕ Add service",
    "btn.edit_price": "💰 Change price",
    "btn.edit_duration": "⏱ Change duration",
    "btn.hide_service": "🙈 Hide from catalog",
    "btn.show_service": "👁 Show in catalog",
    "btn.to_services": "⬅️ Services",
    "btn.add_day_off": "➕ Add day off",
    "btn.remove_day_off": "🗑 Remove {day}",
    "btn.to_days_off": "⬅️ Days off",
    # --- client booking ---
    "booking.no_services": "No services are available right now. Please check back later 🙏",
    "booking.choose_service": "Choose a service:",
    "booking.no_dates": "There are no available dates in the near future 😔",
    "booking.choose_date": "Choose a date:",
    "booking.no_slots": "No free time on {day}",
    "booking.slots": "Free time on {day}:",
    "booking.summary": (
        "Please check your booking:\n\n🧾 {service}\n📅 {when}\n⏱ {duration}\n💰 {price}"
    ),
    "booking.created": ("✅ You're booked!\n\n{booking}\n\nYou can cancel it in «My bookings»."),
    "my.empty": "You have no upcoming bookings.",
    "my.title": "<b>Your bookings:</b>",
    "my.ask_cancel": "Cancel this booking?\n\n{booking}",
    "my.cancelled": "✅ Booking cancelled.",
    # --- services ---
    "service.line": "{name} — {duration}, {price}",
    "service.button": "{name} · {duration} · {price}",
    "service.card": "<b>{name}</b>\nDuration: {duration}\nPrice: {price}\nStatus: {status}",
    "service.status_active": "✅ available for booking",
    "service.status_hidden": "🙈 hidden",
    # --- admin panel ---
    "admin.menu": "⚙️ <b>Admin panel</b>",
    "admin.services_title": "<b>Services</b>",
    "admin.services_empty": "No services yet. Add the first one!",
    "admin.ask_name": "Enter the service name (or /cancel to abort):",
    "admin.ask_duration": "Duration in minutes, e.g. 60:",
    "admin.ask_price": "Price in rubles, e.g. 1500:",
    "admin.service_added": "✅ Service added",
    "admin.ask_new_price": "Enter the new price in rubles (or /cancel):",
    "admin.price_updated": "✅ Price updated",
    "admin.ask_new_duration": (
        "Enter the new duration in minutes (or /cancel).\nExisting bookings will not change."
    ),
    "admin.duration_updated": "✅ Duration updated",
    "admin.choose_date": "Choose a date to see its bookings:",
    "admin.day_title": "<b>Bookings on {day}</b>",
    "admin.day_empty": "No bookings on {day}.",
    "admin.ask_cancel": "Cancel this booking? The client will be notified.\n\n{booking}",
    "admin.booking_cancelled": "✅ Booking cancelled.",
    "admin.days_off_title": "<b>Days off</b>",
    "admin.days_off_empty": "No days off planned.",
    "admin.day_off_removed": "✅ Day off removed.",
    "admin.ask_day_off": "Enter the day off as DD.MM.YYYY (or /cancel):",
    "admin.ask_reason": "Reason (optional). Send «{skip}» to skip:",
    "admin.day_off_added": "✅ Day off added.",
    # --- notifications ---
    "notify.new_booking": "🆕 New booking\n{booking}\n👤 {client}",
    "notify.client_cancelled": "↩️ Client cancelled a booking\n{booking}\n👤 {client}",
    "notify.admin_cancelled": (
        "⚠️ Your booking was cancelled by the administrator:\n{booking}\n\n"
        "You can pick another time via /start."
    ),
    # --- errors ---
    "error.generic": "An error occurred",
    "error.unexpected": "Something went wrong 😔 Please try again or press /start.",
    "error.service_not_found": "Service not found",
    "error.service_inactive": "This service is not available for booking right now",
    "error.date_unavailable": "Booking is not available on this date",
    "error.slot_unavailable": "This time is already taken or unavailable. Please choose another.",
    "error.booking_not_found": "Booking not found or already cancelled",
    "error.booking_already_cancelled": "The booking is already cancelled",
    "error.booking_in_past": "A booking that has already started cannot be cancelled",
    "error.day_off_exists": "This day is already marked as a day off",
    "error.day_off_not_found": "Day off not found",
    "error.day_has_bookings": (
        "There are active bookings on this day ({count}). Cancel them first."
    ),
    "validation.generic": "Invalid data",
    "validation.bad_date": "Invalid date",
    "validation.duration_not_int": "Duration must be a whole number of minutes, e.g. 60",
    "validation.duration_range": "Duration must be between {min} and {max} minutes",
    "validation.price_not_number": "Price must be a number, e.g. 1500 or 1499.90",
    "validation.price_range": "Price must be between 0 and {max}",
    "validation.price_precision": "Price cannot have more than two decimal places",
    "validation.name_empty": "Name cannot be empty",
    "validation.name_too_long": "Name must be at most {max} characters long",
    "validation.date_format": "Enter a valid date as DD.MM.YYYY, e.g. 31.12.2026",
    "validation.day_off_in_past": "A day in the past cannot be made a day off",
    "validation.reason_too_long": "Reason must be at most {max} characters long",
}
