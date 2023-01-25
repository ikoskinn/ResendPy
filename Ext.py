from telethon import TelegramClient, sync
import telethon.tl.types.messages

class TelethonExt:
    async def Connect(self, client: TelegramClient, phone_str: str):
        phone_str = phone_str.replace('+', '').replace(' ', '')

        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone_str)
            me = await client.sign_in(phone_str, input(f'[{phone_str}]: Введите код из Telegram: '))
            print(f'[@{me.username} | {me.phone}]: Успешно залогинились в аккаунт!')
        else:
            me = await client.get_me()
            print(f'[@{me.username} | {me.phone}]: Успешно залогинились в аккаунт!')