# Configuration file for the bot
# Copy this file to config.py and fill in your actual IDs

# Bot token (load from environment variable)
import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Manager IDs (replace with real Telegram user IDs)
# Format: list of Telegram user IDs
# To get user ID: ask user to send any message to bot, check logs or use @userinfobot
ALLOWED_MANAGERS = [
    # Add manager IDs here, example:
    # 123456789,
    # 987654321,
]

# Supply department employees and their product categories
# Format: {employee_name: {username: str, user_id: int, categories: list}}
SUPPLY_EMPLOYEES = {
    'employee_1': {
        'name': 'Employee Name 1',
        'username': '@employee_1',
        'user_id': None,  # Replace with real Telegram ID
        'categories': [
            'лукойл', 'lukoil', 'luk oil',
            'delfin group', 'delfin', 'делфин',
            'mannol', 'маннол',
            'abro', 'абро',
            'decorix', 'декорикс',
            'lavr', 'лавр',
            'стеклоомывающие жидкости', 'стеклоомывайка', 'стеклоомыватель', 'омывайка', 'незамерзайка',
            'хомуты', 'хомут',
            'groz', 'гроз',
            'канистры', 'канистра'
        ]
    },
    'employee_2': {
        'name': 'Employee Name 2',
        'username': '@employee_2',
        'user_id': None,  # Replace with real Telegram ID
        'categories': [
            'роснефть', 'rosneft',
            'акб', 'аккумулятор', 'аккумуляторы', 'battery',
            'тубор', 'tubor',
            'батбаза', 'batbaza',
            'тюмень', 'tyumen',
            'zubr', 'зубр',
            'tungstone', 'тангстоун',
            'wd-40', 'wd40', 'вд-40', 'вдшка',
        ]
    },
    'employee_3': {
        'name': 'Employee Name 3',
        'username': '@employee_3',
        'user_id': None,  # Replace with real Telegram ID
        'categories': [
            'газпромнефть', 'газпром', 'gazpromneft', 'gazprom',
            'mobil', 'мобил',
            'shell', 'шелл',
            'argo', 'арго',
            'zic', 'зик',
            'total', 'тотал',
            'elf', 'эльф',
            'vmpavto', 'вмпавто',
            'texoil', 'тексоил',
            'газ', 'газовое оборудование', 'газовое', 'гбо'
        ]
    },
    'employee_4': {
        'name': 'Employee Name 4',
        'username': '@employee_4',
        'user_id': None,  # Replace with real Telegram ID
        'categories': [
            'тосол синтез', 'тосол', 'tosol',
            'idemitsu', 'идемитсу', 'zepro touring', 'zepro',
            'kerry', 'kudo', 'керри', 'кудо',
            'goodyear', 'azard', 'гудиер', 'азард',
            'avs', 'авс', 'автоаксессуары', 'автолампы', 'лампы',
            'растворители', 'растворитель', 'керосин', 'ацетон',
            'сож', 'эра-м', 'era-m', 'partner', 'партнер',
            'svejo', 'свежо', 'ароматизаторы', 'ароматизатор',
            'ветошь', 'бутылки', 'бутылка', 'перчатки', 'перчатка'
        ]
    },
    'employee_5': {
        'name': 'Employee Name 5',
        'username': '@employee_5',
        'user_id': None,  # Replace with real Telegram ID
        'categories': [
            'обнинскоргсинтез', 'обнинск', 'obninsk',
            'kixx', 'кикс',
            'заказные', 'заказная', 'заказной', 'заказное',
            'тех жидкости', 'технические жидкости',
            'масла прочие', 'прочие масла',
            'автохимия прочая', 'прочая автохимия',
            'аксессуары прочие', 'прочие аксессуары',
            'смазки прочие', 'прочие смазки'
        ]
    }
}

# Helper function to get all supply employee IDs
def get_supply_employee_ids():
    """Get list of all supply employee user IDs"""
    ids = []
    for employee_data in SUPPLY_EMPLOYEES.values():
        if employee_data['user_id']:
            ids.append(employee_data['user_id'])
    return list(set(ids))  # Remove duplicates


# JSON file paths
ACTIVE_REQUESTS_FILE = '/path/to/data/active_requests.json'
HISTORY_FILE = '/path/to/data/history.json'

