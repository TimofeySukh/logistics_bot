# MAKON Logistics Bot

## ⚠️ Proprietary Software - All Rights Reserved

**Copyright © 2025. All rights reserved.**

This software is proprietary and confidential. Unauthorized use, reproduction, or distribution is strictly prohibited. This repository is maintained for portfolio demonstration purposes only.

---

## Overview

Internal Telegram bot for a Russian logistics company that automates communication between sales managers and supply department employees. The bot intelligently routes product delivery inquiries to the appropriate specialist based on product categories.

---

## Technical Stack

- **Python 3.x** with python-telegram-bot library
- **JSON-based** data persistence
- **Multi-state** conversation handler
- **Fuzzy matching** algorithm for product categorization

---

## Project Structure

### **bot.py** (713 lines)
Main application handling:
- Conversation flow and state management
- Role-based access control (managers/employees)
- Request routing and notifications
- JSON data persistence for active requests and history

### **category_matcher.py** (110 lines)
Smart matching module with:
- Case-insensitive text matching
- Cyrillic/Latin transliteration support
- Substring and multi-word matching
- Automatic employee assignment by product category

### **config.example.py** (119 lines)
Configuration template defining:
- Bot token and authentication
- Authorized user IDs (managers and supply staff)
- Employee-to-category mappings (oil brands, batteries, chemicals, accessories, etc.)
- Data storage paths

### **requirements.txt**
- `python-telegram-bot==20.7`
- `python-dotenv==1.0.0`

---

## How It Works

1. Manager describes product (e.g., "Mobil 5W-40")
2. Bot matches keywords to employee categories
3. Question forwarded to responsible supply employee
4. Employee responds with delivery information
5. Response delivered back to manager
6. Request archived in history

---

## Key Features

- **Intelligent routing**: Automatically finds the right employee for each product
- **Ambiguity handling**: Shows category selection when multiple matches found
- **Request tracking**: Maintains active requests and completion history
- **Bilingual support**: Handles both Russian and transliterated product names
- **Access control**: Whitelist-based user authentication

---

## Data Files

- **active_requests.json**: Currently pending inquiries
- **history.json**: Completed request archive

---

**Note**: This is a portfolio project showcasing practical application of Telegram Bot API, natural language processing, and workflow automation in a real business environment.
