#-*- coding: UTF-8 -*-
import asyncio

from telethon import TelegramClient, events
import telethon.tl.types.messages
import configparser

from SQLite.sqliteManager import SQLite

import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

DB = SQLite('ResendDB')                               # БД, название файла.
config = configparser.ConfigParser()

api_id = int(config['Main']['api_id'])                # API ID и API HASH вы должны получить самостоятельно
api_hash = config['Main']['api_hash']
admin_password = config['Main']['password']           # Пароль требуемый чтобы бот вам отвечал.
channelToName = config['Main']['channel']             # Юзернейм канала на который бот будет пересылать посты.





with TelegramClient('name', api_id, api_hash) as client:
   deletingChannels = False

   @client.on(events.NewMessage(pattern=admin_password))          # Вызывается после отправки пароля в ЛС боту.
   async def handler(event):
      sender = await event.get_sender()
      if DB.IsAdmin(sender):
         await event.reply('Вы уже являетесь админом!')
      else:
         DB.AddAdmin(sender)
         await event.reply('Добавил вас в список администраторов в БД!')

   @client.on(events.NewMessage(outgoing=False, pattern='@.*'))    # Метод для добавления каналов откуда бот будет пересылать посты.
   async def handler(event):
      if deletingChannels is False:
         sender = await event.get_sender()
         if DB.IsAdmin(sender):
            channels = str(event.message.text).split('\n')

            lastPostId = -1
            addedChannelsCount = 0

            for channel in channels:
               try:
                  channelFrom = await client.get_entity(channel)
                  if type(channelFrom) is telethon.tl.types.Channel:
                     if not DB.ChannelExists(channelFrom):
                        async for message in client.iter_messages(channelFrom):
                           lastPostId = message.id
                           break
                        DB.AddChannel(channelFrom, lastPostId)
                        addedChannelsCount = addedChannelsCount + 1
                     else:
                        await event.respond(f'Канал {channel} уже есть в БД!')
                  else:
                     await event.respond(f'Объект {channel} не является каналом!')
               except Exception as e:
                  print(str(e))
                  await event.respond(f'Не нашли канал {channel}!')


            if addedChannelsCount > 1:
               await event.reply(f'Добавили каналы ({addedChannelsCount}) в список пересылаемых!')
            elif addedChannelsCount == 1:
               await event.reply(f'Добавили 1 канал  в список пересылаемых!')
            else:
               await event.reply(f'Не добавили ни одного канала в список пересылаемых!')

         else:
            print('Написал не админ!')

   @client.on(events.NewMessage(outgoing=False, pattern='/del'))  # Метод для удаления каналов из БД, откуда бот берет посты.
   async def handler(event):
      sender = await event.get_sender()
      if DB.IsAdmin(sender):
         channels = DB.GetAllChannels()
         channelsStr = ''

         for channel in channels:
            channelsStr = f'@{channel[1]}\n'
         await event.reply(f'Напишите канал/каналы(через перенос строки) для удаления из БД\nСписок каналов:\n' + channelsStr)
         global deletingChannels
         deletingChannels = True
      else:
         print('Написал не админ!')

   @client.on(events.NewMessage(outgoing=False, pattern='/start')) # Приветственное сообщение, работает только для администраторов.
   async def handler(event):
      sender = await event.get_sender()
      if DB.IsAdmin(sender):
         channels = DB.GetAllChannels()
         channelsStr = ''

         for channel in channels:
            channelsStr = f'@{channel[1]}\n'
         await event.reply(f'Напишите канал/каналы(через перенос строки) для удаления из БД\nСписок каналов:\n' + channelsStr)
         global deletingChannels
         deletingChannels = True
      else:
         print('Написал не админ!')

   @client.on(events.NewMessage())
   async def handler(event):  # Хендлер для всех сообщений боту,
      global deletingChannels
      sender = await event.get_sender()
      if DB.IsAdmin(sender):
         if deletingChannels is True and event.message.text != '/del': # Если администратор отправил /del, то затем ему нужно отправить @юзернеймы каналов для удаления.
            channels = str(event.message.text).split('\n')
            for channel in channels:
               try:
                  channel = await client.get_entity(channel)
                  if type(channel) is telethon.tl.types.Channel:
                     DB.DeleteChannel(channel)
                     await event.respond(f'Удалили канал {channel.username} из пересылаемых!')
                  else:
                     await event.respond(f'{channel} не является каналом поэтому пропускаем!')
               except Exception as e:
                  print(str(e))
                  await event.respond(f'Не нашли канал {channel}!')
            deletingChannels = False
      else:
         print('Написал не админ!')

   async def forward_posts(): # Основной метод для пересылки постов
      while True:
         print(f"Начинаем процесс пересылки постов")
         channelTo = await client.get_entity(channelToName)
         results = DB.GetAllChannels()
         for result in results:
             channelFrom = await client.get_entity(result[0])
             last_post_forwarded_id = result[2]
             last_post_id = -1

             last_grouped_id = -1

             messagesToForward = []

             async for message in client.iter_messages(channelFrom):
                if last_post_id == -1:
                   last_post_id = message.id

                if message.id > last_post_forwarded_id:  # Нужно компоновать сообщения в списки в списках, чтобы пересылать сообщения с несколькими медиа как одно целое.
                   if message.grouped_id == last_grouped_id and message.grouped_id != 0:
                       messagesToForward[-1].append(message)
                   else:
                       messagesToForward.append([message])
                   last_grouped_id = message.grouped_id
                else:
                   break

             if len(messagesToForward) > 0:
                messagesToForward.reverse()
                for messages in messagesToForward:
                   messages.reverse()
                   await client.forward_messages(channelTo, messages, channelFrom)

                last_post_forwarded_id = messagesToForward[-1][-1].id
                DB.UpdateLastPostId(channelFrom, last_post_forwarded_id)
                print(f"Переслали {len(messagesToForward)} с канала {channelFrom.username}.")
             else:
                print(f"У канала {channelFrom.username} нет новых постов.")

         print(f"Закончили цикл пересылки постов. Повторяем через 10 секунд.")


   loop = asyncio.get_event_loop()
   loop.create_task(forward_posts())
   client.run_until_disconnected()
