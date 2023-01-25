#-*- coding: UTF-8 -*-
import asyncio
import os
import time
import typing
from glob import glob

from telethon import TelegramClient, events
import telethon.tl.types.messages

import configparser

import psycopg2
import Postgre.postgreManager

from Ext import TelethonExt

import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


config = configparser.ConfigParser()
config.read("settings.ini")

api_id = int(config['Main']['api_id'])                             # API ID и API HASH вы должны получить самостоятельно
api_hash = config['Main']['api_hash']
admin_password = config['Main']['password']                        # Пароль требуемый чтобы бот вам отвечал.
channelToName = config['Main']['channel']                          # Юзернейм канала на который бот будет пересылать посты.
forwardingCooldown = int(config['Main']['forwarding_cooldown'])    # Ожидание после цикла пересылки всех постов.
max_channels_per_acc = int(config['Main']['max_channels_per_acc']) # Максимальное количество каналов которое один аккаунт будет проверять.

# Multi Accounts section

phones = config['MultiAccounts']['phones'].split(',')              # Номера телефонов соответствующие каждому аккаунту.
                                                                   # Требуется чтобы не вводить номера телефонов вручную в командной строке. Но смс коды вводить придется.

saved_channels = {}

if api_id == '' or api_hash == '' or channelToName == '':
   print('Проверьте настройки программы. Есть пустые поля которые необходимы быть заполнеными.')
   input("Нажмите любую клавишу для выхода..")
   exit()


pDB = Postgre.postgreManager.Postgre(
   user=config['Postgre']['user'],
   password=config['Postgre']['password'],
   host=config['Postgre']['host'],
   port=config['Postgre']['port'],
   database=config['Postgre']['database']
)

async def forward_posts(client: telethon.client.TelegramClient, phone: str):  # Основной метод для пересылки постов
   admin_permission = False

   global saved_channels

   await TelethonExt().Connect(client, phone)

   async with client:
      me = await client.get_me()
      channelTo = await client.get_entity(channelToName)
      print(
         f'[@{me.username} | {me.phone}]: Запустили метод пересылки постов')
      while True:
         try:
            permissions = await client.get_permissions(channelTo, me)
            if not permissions.is_admin:
               admin_permission = False
            else:
               admin_permission = True
         except:
            admin_permission = False
         if admin_permission:
            t = pDB.GetAndUpdateChannels(forwardingCooldown, max_channels_per_acc)
            if t is not None:
               if len(t) > 0:
                  print(f"[@{me.username} | {me.phone}]: Начинаем процесс пересылки постов")
                  for result in t:
                     try:
                        if result[1] not in saved_channels:
                           saved_channels[result[1]] = await client.get_entity(result[1])

                        channelFrom = saved_channels[result[1]]

                     except Exception as e:
                        print(str(e))
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
                        pDB.UpdateLastPostId(channelFrom, last_post_forwarded_id)
                        print(f"[@{me.username} | {me.phone}]: Переслали {len(messagesToForward)} с канала @{channelFrom.username}.")
                     else:
                        print(f"[@{me.username} | {me.phone}]: У канала @{channelFrom.username} нет новых постов.")

                  print(f"[@{me.username} | {me.phone}]: Закончили цикл пересылки постов. Повторяем через {forwardingCooldown} секунд.")
               else:
                  print(
                     f"[@{me.username} | {me.phone}]: Каналов надлежащих проверке не нашлось. Пробуем через {forwardingCooldown} секунд.")
         else:
            print(
               f'[@{me.username} | {me.phone}]: Нет прав админа у аккаунта на канале @{channelToName}. Пробуем еще раз через {forwardingCooldown} секунд.')
         await asyncio.sleep(forwardingCooldown)


clients_phones = config['MultiAccounts']['phones'].split(',')
clients = [TelegramClient(phone.replace('+', '').replace(' ', ''), api_id, api_hash) for phone in clients_phones]

MAIN_CLIENT = clients[0] # ADDED TO COMPILE PROJECT WITH AUTO-PY-TO-EXE

clients_jobs = [forward_posts(client, clients_phones[clients.index(client)]) for client in clients]

async def main():
   await asyncio.gather(
      *clients_jobs
   )

   await TelethonExt().Connect(clients[0], clients_phones[0])
   clients[0].run_until_disconnected()

deletingChannels = False

@MAIN_CLIENT.on(events.NewMessage(pattern=admin_password))           # Вызывается после отправки пароля в ЛС боту.
async def handler(event):
   sender = await event.get_sender()
   if pDB.IsAdmin(sender):
      await event.reply('Вы уже являетесь админом!')
   else:
      pDB.AddAdmin(sender)
      await event.reply('Добавил вас в список администраторов в БД!')

@MAIN_CLIENT.on(events.NewMessage(outgoing=False, pattern='@.*'))    # Метод для добавления каналов откуда бот будет пересылать посты.
async def handler(event):
   if deletingChannels is False:
      sender = await event.get_sender()
      if pDB.IsAdmin(sender):
         channels = str(event.message.text).split('\n')

         lastPostId = -1
         addedChannelsCount = 0

         for channel in channels:
            try:
               channelFrom = await clients[0].get_entity(channel)
               if type(channelFrom) is telethon.tl.types.Channel:
                  if not pDB.ChannelExists(channelFrom):
                     async for message in clients[0].iter_messages(channelFrom):
                        lastPostId = message.id
                        break
                     pDB.AddChannel(channelFrom, lastPostId)
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
         pass

@MAIN_CLIENT.on(events.NewMessage(outgoing=False, pattern='/del'))   # Метод для удаления каналов из БД, откуда бот берет посты.
async def handler(event):
   sender = await event.get_sender()
   if pDB.IsAdmin(sender):
      channels = pDB.GetAllChannels()
      channelsStr = ''

      for channel in channels:
         channelsStr = f'@{channel[1]}\n'
      await event.reply(f'Напишите канал/каналы(через перенос строки) для удаления из БД\nСписок каналов:\n' + channelsStr)
      global deletingChannels
      deletingChannels = True
   else:
      pass

@MAIN_CLIENT.on(events.NewMessage(outgoing=False, pattern='/start')) # Приветственное сообщение, работает только для администраторов.
async def handler(event):
   sender = await event.get_sender()
   if pDB.IsAdmin(sender):
      channels = pDB.GetAllChannels()
      channelsStr = ''

      for channel in channels:
         channelsStr = f'@{channel[1]}\n'
      await event.reply(f'Напишите канал/каналы(через перенос строки) для удаления из БД\nСписок каналов:\n' + channelsStr)
      global deletingChannels
      deletingChannels = True
   else:
      pass

@MAIN_CLIENT.on(events.NewMessage(outgoing=False, pattern='/all'))   # Получить список всех каналов.
async def handler(event):
   sender = await event.get_sender()
   if pDB.IsAdmin(sender):
      channels = pDB.GetAllChannels()
      channelsStr = ''

      for channel in channels:
         if channel == channels[-1]:
            channelsStr = channelsStr + f'@{channel[1]}'
         else:
            channelsStr = channelsStr + f'@{channel[1]}, '
      await event.reply(f'Список каналов:\n' + channelsStr)
   else:
      pass

@MAIN_CLIENT.on(events.NewMessage())
async def handler(event):  # Хендлер для всех сообщений боту,
   global deletingChannels
   sender = await event.get_sender()
   if pDB.IsAdmin(sender):
      if deletingChannels is True and event.message.text != '/del': # Если администратор отправил /del, то затем ему нужно отправить @юзернеймы каналов для удаления.
         channels = str(event.message.text).split('\n')
         for channel in channels:
            try:
               channel = await clients[0].get_entity(channel)
               if type(channel) is telethon.tl.types.Channel:
                  pDB.DeleteChannel(channel)
                  await event.respond(f'Удалили канал {channel.username} из пересылаемых!')
               else:
                  await event.respond(f'{channel} не является каналом поэтому пропускаем!')
            except Exception as e:
               print(str(e))
               await event.respond(f'Не нашли канал {channel}!')
         deletingChannels = False
   else:
      pass


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
