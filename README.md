# Proxy Bot

Proxy Bot is a Telegram bot that helps users manage and use proxy servers. It provides functionalities to get new proxies, check current proxies, and offers a simple interface for users to interact with proxy services. To retrieve proxy data, the open source free API service proxyscrape.com is used. To store data, a local database is created using SQLite. 

## Features

- Get a new random proxy
- Check current assigned proxy
- Periodic update of proxy list
- Simple user interface with inline buttons

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/proxy-bot.git
   cd proxy-bot
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Telegram Bot Token:
   - Create a new bot via BotFather on Telegram
   - Copy the token and paste it in a new file named `config.py`:
     ```python
     TOKEN = 'your_bot_token_here'
     ```

5. Initialize the database:
   ```
   python import_proxies.py
   ```

## Usage

Run the bot:
```
python bot.py
```

The bot will start and be ready to receive commands on Telegram.

## Commands

- `/start` - Start the bot and get the main menu
- `📜 Main Menu` - Display the main menu
- `🔍 Check Proxy` - Check your current assigned proxy
- `🆕 Get Proxy` - Get a new random proxy
- `❓ Help` - Display help information

## Project Structure

- `bot.py` - Main bot file, contains the entry point
- `db_utils.py` - Database utility functions
- `handlers.py` - Command handlers for the bot
- `import_proxies.py` - Script to import and update proxies
- `test_all.py` - Test suite for the project

## Testing

Run the tests using pytest:
```
pytest test_all.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
