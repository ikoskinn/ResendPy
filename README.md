# ResendPy
Python bot created on Telethon, can forward messages from another channels to yours. It uses Telegram accounts, not bots.


# HOW TO START

1. You need to get your API_ID and API_HASH on https://my.telegram.org/auth and set it in settings.
2. You need to create PostgreSQL database(you can run it locally) and set connection parameters in settings.
3. Bot needs your channel's username to forward messages there. Set your channel's username in settings.ini
4. Parameter 'phones' in settings needed to filled at least with one phone number of Telegram account. You can separate multiple phone numbers with ','. ONLY FIRST ACCOUNT OPERATES COMMANDS.
5. Start script and login to each account (you need to input Telegram code you've got). Write a message with password which you've set in settings, only then you can use commands like '/all', '/del' etc.

# HOW TO USE

- You can add channels for forwarding, just send them by '@'. Example: @username or you can send multiple channels just split them by enter key.
- You can delete channels you've added. Just send to account '/del', then send usernames of channels.
