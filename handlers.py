import asyncio
import aiosqlite
import datetime
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db_utils import (
    get_assigned_proxies_and_language_code,
    assign_proxy,
    replace_proxy,
    get_db_path,
    get_proxy_info  
)
from import_proxies import fetch_proxies, import_proxies


def register_handlers(bot: AsyncTeleBot):
    # Create inline keyboard with buttons
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.row(InlineKeyboardButton('🔍 Check Proxy', callback_data='/check_proxy'),
                        InlineKeyboardButton('🆕 Get Proxy', callback_data='/get_proxy'))
    inline_keyboard.row(InlineKeyboardButton('❓ Help', callback_data='/help'))

    # Create keyboard with "Main Menu" button
    main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu_keyboard.add(KeyboardButton('📜 Main Menu'))

    @bot.message_handler(commands=['start'])
    async def handle_start(message):
        """Handle the /start command."""
        user_id = message.chat.id
        language_code = message.from_user.language_code
        await bot.send_message(
            message.chat.id,
            'Welcome to Proxy Bot! 🌐\n'
            'I will help you obtain and manage your proxy servers.\n'
            'Use the buttons below to interact with me, or press "📜 Main Menu" if you need to call the menu again.',
            reply_markup=main_menu_keyboard
        )
        await bot.send_message(
            message.chat.id,
            'Select an option from the menu below:',
            reply_markup=inline_keyboard
        )
        await assign_proxy(user_id, None, language_code)

    @bot.message_handler(func=lambda message: message.text == '📜 Main Menu')
    async def handle_main_menu(message):
        """Handle the "Main Menu" button press."""
        await bot.send_message(
            message.chat.id,
            'Select an option from the menu below:',
            reply_markup=inline_keyboard
        )

    @bot.callback_query_handler(func=lambda call: True)
    async def callback_query(call):
        """Handle callback queries from inline keyboard buttons."""
        if call.data == '/check_proxy':
            await handle_check_proxy(call.message)
        elif call.data == '/get_proxy':
            await handle_get_proxy(call.message)
        elif call.data == '/help':
            await handle_help(call.message)

    async def handle_check_proxy(message):
        """Handle the "Check Proxy" button press."""
        user_id = message.chat.id
        assigned_proxies, _ = await get_assigned_proxies_and_language_code(user_id)
        if assigned_proxies:
            current_proxy = assigned_proxies[-1]  # Use the last (newest) proxy as the active one
            proxy_info = 'Protocol: {}\nIP Address: {}\nPort: {}\nCountry Code: {}\nCountry: {}\nAnonymity: {}\nHTTPS: {}\nLatency: {}ms\nLast Checked: {}'.format(
                current_proxy['protocol'],
                current_proxy['ip'],
                current_proxy['port'],
                current_proxy['country_code'],
                current_proxy['country'],
                current_proxy['anonymity'],
                current_proxy['https'],
                int(current_proxy['latency']),
                datetime.datetime.fromtimestamp(current_proxy['last_checked']).strftime('%Y-%m-%d %H:%M:%S') if current_proxy['last_checked'] else 'N/A'
            )
            previously_used_proxies = assigned_proxies[:-1]  # Exclude the current proxy
            previously_used_proxies_info = '\n'.join([f"{proxy['protocol']} {proxy['ip']}:{proxy['port']}" for proxy in previously_used_proxies])
            
            await bot.send_message(message.chat.id, f'✅ Your current active proxy:\n\n{proxy_info}\n\nPreviously used proxies:\n{previously_used_proxies_info}', reply_markup=main_menu_keyboard)
        else:
            await bot.send_message(message.chat.id, '❌ You do not have any assigned proxies. Use Get proxy to get one.', reply_markup=main_menu_keyboard)

            

    async def handle_get_proxy(message):
        """Handle the "Get Proxy" button press."""
        user_id = message.chat.id
        language_code = message.from_user.language_code
        assigned_proxies, _ = await get_assigned_proxies_and_language_code(user_id)

        new_proxy = await replace_proxy(user_id, [proxy['proxy'] for proxy in assigned_proxies])
        if new_proxy:
            new_proxy_info = await get_proxy_info(new_proxy)
            if new_proxy_info:
                await assign_proxy(user_id, new_proxy, language_code)
                proxy_info_str = 'Protocol: {}\nIP Address: {}\nPort: {}\nCountry Code: {}\nCountry: {}\nAnonymity: {}\nHTTPS: {}\nLatency: {}ms\nLast Checked: {}'.format(
                    new_proxy_info['protocol'],
                    new_proxy_info['ip'],
                    new_proxy_info['port'],
                    new_proxy_info['country_code'],
                    new_proxy_info['country'],
                    new_proxy_info['anonymity'],
                    new_proxy_info['https'],
                    int(new_proxy_info['latency']),
                    datetime.datetime.fromtimestamp(new_proxy_info['last_checked']).strftime('%Y-%m-%d %H:%M:%S') if new_proxy_info['last_checked'] else 'N/A'
                )
                await bot.send_message(message.chat.id, f'🎉 You have been assigned a new proxy:\n\n{proxy_info_str}', reply_markup=main_menu_keyboard)
            else:
                await bot.send_message(message.chat.id, '😢 Unfortunately, there are no available proxies at the moment. Please try again later.', reply_markup=main_menu_keyboard)
        else:
            await bot.send_message(message.chat.id, '😢 Unfortunately, there are no available proxies at the moment. Please try again later.', reply_markup=main_menu_keyboard)


    async def handle_help(message):
        """Handle the "Help" button press."""
        await bot.send_message(message.chat.id, 
                               '📚 Here is a list of available commands:\n'
                               '🔍 Check Proxy - Check your current proxy.\n'
                               '🆕 Get Proxy - Get a new random proxy.\n'
                               '❓ Help - Show this help message.',
                               reply_markup=main_menu_keyboard)