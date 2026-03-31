"""
Logistics Bot - "When will the product arrive?"
Bot for sales managers to ask supply department about product delivery times.
"""

import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from config import (
    BOT_TOKEN,
    ALLOWED_MANAGERS,
    SUPPLY_EMPLOYEES,
    ACTIVE_REQUESTS_FILE,
    HISTORY_FILE,
    get_supply_employee_ids
)
from category_matcher import (
    find_employee_by_category,
    get_category_buttons,
    get_employee_by_key
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PRODUCT = 1
WAITING_FOR_CATEGORY_CHOICE = 2
WAITING_FOR_EMPLOYEE_RESPONSE = 3

# User data keys
USER_STATE_KEY = 'state'
PENDING_REQUEST_KEY = 'pending_request'


# ==================== JSON Data Management ====================

def load_json_file(filepath):
    """Load data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from {filepath}")
        return {}


def save_json_file(filepath, data):
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")


def get_active_requests():
    """Get all active requests"""
    return load_json_file(ACTIVE_REQUESTS_FILE)


def save_active_requests(data):
    """Save active requests"""
    save_json_file(ACTIVE_REQUESTS_FILE, data)


def get_history():
    """Get request history"""
    return load_json_file(HISTORY_FILE)


def save_history(data):
    """Save request history"""
    save_json_file(HISTORY_FILE, data)


def add_active_request(user_id, username, product_query, employee_key, employee_name, employee_user_id):
    """Add new active request"""
    active_requests = get_active_requests()
    
    request_data = {
        'user_id': user_id,
        'username': username,
        'product_query': product_query,
        'employee_key': employee_key,
        'employee_name': employee_name,
        'employee_user_id': employee_user_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'waiting'
    }
    
    active_requests[str(user_id)] = request_data
    save_active_requests(active_requests)
    return request_data


def remove_active_request(user_id):
    """Remove active request for user"""
    active_requests = get_active_requests()
    if str(user_id) in active_requests:
        del active_requests[str(user_id)]
        save_active_requests(active_requests)


def get_user_active_request(user_id):
    """Get active request for specific user"""
    active_requests = get_active_requests()
    return active_requests.get(str(user_id))


def find_request_by_employee(employee_user_id):
    """Find active request by employee user_id"""
    active_requests = get_active_requests()
    for user_id, request_data in active_requests.items():
        if request_data.get('employee_user_id') == employee_user_id:
            return user_id, request_data
    return None, None


def add_to_history(request_data, response_text):
    """Add completed request to history"""
    history = get_history()
    
    history_entry = {
        **request_data,
        'response': response_text,
        'completed_at': datetime.now().isoformat()
    }
    
    # Use timestamp as key
    timestamp_key = datetime.now().isoformat()
    history[timestamp_key] = history_entry
    save_history(history)


# ==================== Helper Functions ====================

def is_manager(user_id, username):
    """Check if user is allowed manager"""
    # For now, allow everyone if ALLOWED_MANAGERS is empty (for testing)
    if not ALLOWED_MANAGERS:
        return True
    
    # Check by user_id or username
    return user_id in ALLOWED_MANAGERS or username in ALLOWED_MANAGERS


def format_category_keyboard():
    """Create keyboard with category options"""
    buttons = get_category_buttons()
    
    # Create keyboard layout (1 button per row)
    keyboard = [[button[1]] for button in buttons]
    
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


# ==================== Bot Handlers ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Check if user is a supply employee (they can only respond, not ask questions)
    supply_employee_ids = get_supply_employee_ids()
    if user.id in supply_employee_ids:
        await update.message.reply_text(
            "Вы являетесь сотрудником Отдела Снабжения. "
            "Вы можете только отвечать на вопросы менеджеров, отвечая (reply) на сообщения бота."
        )
        return ConversationHandler.END
    
    # Check if user is allowed manager
    if not is_manager(user.id, user.username):
        await update.message.reply_text(
            "Sorry, this bot is only available for authorized managers."
        )
        return ConversationHandler.END
    
    # Check if user already has pending request
    active_request = get_user_active_request(user.id)
    if active_request:
        await update.message.reply_text(
            "У вас уже есть активный запрос. Пожалуйста, дождитесь ответа от сотрудника Отдела Снабжения.\n\n"
            f"Ваш вопрос: {active_request['product_query']}\n"
            f"Ожидается ответ от: {active_request['employee_name']}"
        )
        return ConversationHandler.END
    
    # Ask for product
    await update.message.reply_text(
        "Какой товар вас интересует?",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return WAITING_FOR_PRODUCT


async def handle_product_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's product query"""
    user = update.effective_user
    product_query = update.message.text
    
    # Check if user is a supply employee (they can only respond, not ask questions)
    supply_employee_ids = get_supply_employee_ids()
    if user.id in supply_employee_ids:
        await update.message.reply_text(
            "Вы являетесь сотрудником Отдела Снабжения. "
            "Вы можете только отвечать на вопросы менеджеров, отвечая (reply) на сообщения бота."
        )
        return ConversationHandler.END
    
    # Check if user already has pending request
    active_request = get_user_active_request(user.id)
    if active_request:
        await update.message.reply_text(
            "У вас уже есть активный запрос. Пожалуйста, дождитесь ответа от сотрудника Отдела Снабжения.\n\n"
            f"Ваш вопрос: {active_request['product_query']}\n"
            f"Ожидается ответ от: {active_request['employee_name']}"
        )
        return ConversationHandler.END
    
    # Try to find responsible employee
    employee = find_employee_by_category(product_query)
    
    if employee:
        # Found responsible employee - send request
        return await send_request_to_employee(update, context, product_query, employee)
    else:
        # Could not determine category - ask user to choose
        await update.message.reply_text(
            "Не могу однозначно определить категорию товара. Пожалуйста, выберите подходящую категорию:",
            reply_markup=format_category_keyboard()
        )
        
        # Save product query for later
        context.user_data['product_query'] = product_query
        
        return WAITING_FOR_CATEGORY_CHOICE


async def handle_category_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's manual category selection"""
    user = update.effective_user
    choice_text = update.message.text
    product_query = context.user_data.get('product_query', 'Не указано')
    
    # Find which employee matches the choice
    buttons = get_category_buttons()
    selected_employee_key = None
    
    for employee_key, display_text in buttons:
        if display_text == choice_text:
            selected_employee_key = employee_key
            break
    
    if not selected_employee_key:
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из предложенных вариантов:",
            reply_markup=format_category_keyboard()
        )
        return WAITING_FOR_CATEGORY_CHOICE
    
    # Get employee data
    employee = get_employee_by_key(selected_employee_key)
    
    if not employee:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте еще раз с командой /start"
        )
        return ConversationHandler.END
    
    # Send request to employee
    return await send_request_to_employee(update, context, product_query, employee)


async def send_request_to_employee(update: Update, context: ContextTypes.DEFAULT_TYPE, product_query, employee):
    """Send request to supply department employee"""
    user = update.effective_user
    
    # Check if employee user_id is set
    if not employee['user_id']:
        await update.message.reply_text(
            f"К сожалению, контакт сотрудника {employee['name']} еще не настроен в системе. "
            "Пожалуйста, обратитесь к администратору.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Add to active requests
    add_active_request(
        user_id=user.id,
        username=user.username or user.first_name,
        product_query=product_query,
        employee_key=employee['key'],
        employee_name=employee['name'],
        employee_user_id=employee['user_id']
    )
    
    # Send message to employee
    employee_message = (
        f"📦 Новый вопрос от менеджера\n\n"
        f"От: @{user.username or user.first_name}\n"
        f"Вопрос: {product_query}\n\n"
        f"Пожалуйста, ответьте на это сообщение, и ваш ответ будет автоматически отправлен менеджеру."
    )
    
    try:
        sent_message = await context.bot.send_message(
            chat_id=employee['user_id'],
            text=employee_message
        )
        
        # Store message_id for tracking replies
        active_requests = get_active_requests()
        active_requests[str(user.id)]['employee_message_id'] = sent_message.message_id
        save_active_requests(active_requests)
        
    except Exception as e:
        logger.error(f"Error sending message to employee {employee['name']}: {e}")
        remove_active_request(user.id)
        await update.message.reply_text(
            f"Не удалось отправить запрос сотруднику {employee['name']}. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Create inline keyboard with cancel button
    keyboard = [[InlineKeyboardButton("❌ Отменить запрос", callback_data=f"cancel_request_{user.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Confirm to user
    confirmation_message = await update.message.reply_text(
        f"✅ Ваш вопрос отправлен сотруднику {employee['name']}.\n"
        f"Ожидайте ответа. Как только получу ответ, сразу перешлю вам.",
        reply_markup=reply_markup
    )
    
    # Store confirmation message_id for later removal of button
    active_requests = get_active_requests()
    active_requests[str(user.id)]['manager_message_id'] = confirmation_message.message_id
    save_active_requests(active_requests)
    
    return ConversationHandler.END


async def handle_employee_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle response from supply department employee"""
    employee_user_id = update.effective_user.id
    
    # Check if this is a reply to bot's message
    if not update.message.reply_to_message:
        return
    
    # Check if reply is to our bot
    if update.message.reply_to_message.from_user.id != context.bot.id:
        return
    
    # Find which request this response is for
    manager_user_id, request_data = find_request_by_employee(employee_user_id)
    
    if not manager_user_id or not request_data:
        await update.message.reply_text(
            "Не могу найти соответствующий запрос. Возможно, он уже был обработан."
        )
        return
    
    response_text = update.message.text
    
    # Send response to manager
    try:
        manager_message = (
            f"📬 Ответ от {request_data['employee_name']}:\n\n"
            f"{response_text}\n\n"
            f"По вашему вопросу: {request_data['product_query']}"
        )
        
        await context.bot.send_message(
            chat_id=int(manager_user_id),
            text=manager_message
        )
        
        # Remove cancel button from manager's confirmation message
        manager_message_id = request_data.get('manager_message_id')
        if manager_message_id:
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=int(manager_user_id),
                    message_id=manager_message_id,
                    reply_markup=None
                )
            except Exception as e:
                logger.error(f"Error removing cancel button: {e}")
        
        # Confirm to employee
        await update.message.reply_text(
            "✅ Ваш ответ отправлен менеджеру. Спасибо!"
        )
        
        # Move to history and remove from active
        add_to_history(request_data, response_text)
        remove_active_request(int(manager_user_id))
        
    except Exception as e:
        logger.error(f"Error sending response to manager: {e}")
        await update.message.reply_text(
            "Произошла ошибка при отправке ответа менеджеру. Пожалуйста, попробуйте еще раз."
        )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation"""
    await update.message.reply_text(
        "Операция отменена. Используйте /start для нового запроса.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def handle_cancel_request_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel request button press"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Check if user has active request
    active_request = get_user_active_request(user.id)
    
    if not active_request:
        await query.edit_message_text(
            "❌ Активный запрос не найден. Возможно, он уже был обработан."
        )
        return
    
    # Get employee info
    employee_name = active_request['employee_name']
    employee_user_id = active_request.get('employee_user_id')
    product_query = active_request['product_query']
    
    # Remove from active requests
    remove_active_request(user.id)
    
    # Notify employee that request was cancelled
    if employee_user_id:
        try:
            await context.bot.send_message(
                chat_id=employee_user_id,
                text=f"ℹ️ Менеджер @{user.username or user.first_name} отменил свой запрос:\n\"{product_query}\""
            )
        except Exception as e:
            logger.error(f"Error notifying employee about cancellation: {e}")
    
    # Confirm cancellation to manager
    await query.edit_message_text(
        f"🚫 Ваш запрос отменен.\n\n"
        f"Вопрос: {product_query}\n"
        f"Был направлен: {employee_name}\n\n"
        f"Просто напишите новый вопрос для отправки."
    )


async def handle_direct_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct questions from managers without /start"""
    user = update.effective_user
    
    # Check if user is a supply employee (they can only respond, not ask questions)
    supply_employee_ids = get_supply_employee_ids()
    if user.id in supply_employee_ids:
        # Don't respond - they should only reply to bot messages
        return
    
    # Check if user is allowed manager
    if not is_manager(user.id, user.username):
        await update.message.reply_text(
            "Sorry, this bot is only available for authorized managers."
        )
        return
    
    # Check if user already has pending request
    active_request = get_user_active_request(user.id)
    if active_request:
        await update.message.reply_text(
            "У вас уже есть активный запрос. Пожалуйста, дождитесь ответа от сотрудника Отдела Снабжения.\n\n"
            f"Ваш вопрос: {active_request['product_query']}\n"
            f"Ожидается ответ от: {active_request['employee_name']}"
        )
        return
    
    # Process the question directly
    product_query = update.message.text
    
    # Try to find responsible employee
    employee = find_employee_by_category(product_query)
    
    if employee:
        # Found responsible employee - send request
        await send_request_to_employee_direct(update, context, product_query, employee)
    else:
        # Could not determine category - ask user to choose
        await update.message.reply_text(
            "Не могу однозначно определить категорию товара. Пожалуйста, выберите подходящую категорию:",
            reply_markup=format_category_keyboard()
        )
        
        # Save product query for later
        context.user_data['product_query'] = product_query
        context.user_data['awaiting_category'] = True


async def send_request_to_employee_direct(update: Update, context: ContextTypes.DEFAULT_TYPE, product_query, employee):
    """Send request to supply department employee (for direct messages)"""
    user = update.effective_user
    
    # Check if employee user_id is set
    if not employee['user_id']:
        await update.message.reply_text(
            f"К сожалению, контакт сотрудника {employee['name']} еще не настроен в системе. "
            "Пожалуйста, обратитесь к администратору.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Add to active requests
    add_active_request(
        user_id=user.id,
        username=user.username or user.first_name,
        product_query=product_query,
        employee_key=employee['key'],
        employee_name=employee['name'],
        employee_user_id=employee['user_id']
    )
    
    # Send message to employee
    employee_message = (
        f"📦 Новый вопрос от менеджера\n\n"
        f"От: @{user.username or user.first_name}\n"
        f"Вопрос: {product_query}\n\n"
        f"Пожалуйста, ответьте на это сообщение, и ваш ответ будет автоматически отправлен менеджеру."
    )
    
    try:
        sent_message = await context.bot.send_message(
            chat_id=employee['user_id'],
            text=employee_message
        )
        
        # Store message_id for tracking replies
        active_requests = get_active_requests()
        active_requests[str(user.id)]['employee_message_id'] = sent_message.message_id
        save_active_requests(active_requests)
        
    except Exception as e:
        logger.error(f"Error sending message to employee {employee['name']}: {e}")
        remove_active_request(user.id)
        await update.message.reply_text(
            f"Не удалось отправить запрос сотруднику {employee['name']}. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Create inline keyboard with cancel button
    keyboard = [[InlineKeyboardButton("❌ Отменить запрос", callback_data=f"cancel_request_{user.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Confirm to user
    confirmation_message = await update.message.reply_text(
        f"✅ Ваш вопрос отправлен сотруднику {employee['name']}.\n"
        f"Ожидайте ответа. Как только получу ответ, сразу перешлю вам.",
        reply_markup=reply_markup
    )
    
    # Store confirmation message_id for later removal of button
    active_requests = get_active_requests()
    active_requests[str(user.id)]['manager_message_id'] = confirmation_message.message_id
    save_active_requests(active_requests)


async def handle_category_choice_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category choice from keyboard (for direct messages)"""
    user = update.effective_user
    choice_text = update.message.text
    
    # Check if user is awaiting category choice
    if not context.user_data.get('awaiting_category'):
        # Not waiting for category, treat as new question
        await handle_direct_question(update, context)
        return
    
    product_query = context.user_data.get('product_query', 'Не указано')
    
    # Find which employee matches the choice
    buttons = get_category_buttons()
    selected_employee_key = None
    
    for employee_key, display_text in buttons:
        if display_text == choice_text:
            selected_employee_key = employee_key
            break
    
    if not selected_employee_key:
        await update.message.reply_text(
            "Пожалуйста, выберите категорию из предложенных вариантов:",
            reply_markup=format_category_keyboard()
        )
        return
    
    # Get employee data
    employee = get_employee_by_key(selected_employee_key)
    
    if not employee:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте еще раз."
        )
        context.user_data.clear()
        return
    
    # Clear user data
    context.user_data.clear()
    
    # Remove keyboard
    await update.message.reply_text(
        "✓ Категория выбрана",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Send request to employee
    await send_request_to_employee_direct(update, context, product_query, employee)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = (
        "🤖 Бот для запросов о поставках товаров\n\n"
        "Команды:\n"
        "/start - Задать вопрос о товаре\n"
        "/cancel - Отменить текущую операцию\n"
        "/help - Показать эту справку\n\n"
        "Как использовать:\n"
        "1. Просто напишите название товара или категорию\n"
        "2. Дождитесь ответа от сотрудника Отдела Снабжения\n\n"
        "Примечание:\n"
        "- Вы можете задать только один вопрос за раз\n"
        "- Вы можете отменить свой запрос кнопкой \"Отменить запрос\""
    )
    await update.message.reply_text(help_text)


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for managers
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            WAITING_FOR_PRODUCT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_query)
            ],
            WAITING_FOR_CATEGORY_CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_choice)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))
    
    # Handler for cancel request button
    application.add_handler(
        CallbackQueryHandler(handle_cancel_request_button, pattern=r'^cancel_request_')
    )
    
    # Handler for employee responses (replies to bot messages)
    application.add_handler(
        MessageHandler(filters.REPLY & filters.TEXT & ~filters.COMMAND, handle_employee_response)
    )
    
    # Handler for direct questions from managers (without /start)
    # This should be last to not interfere with other handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.REPLY, handle_direct_question)
    )
    
    # Start bot
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

