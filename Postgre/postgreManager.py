import threading
import time

import psycopg2
from psycopg2 import Error

import telethon.tl.types

lock = threading.Lock()


class Postgre:
    connection = None
    cursor = None

    def __init__(self, user, password, host, port, database, phone_number):
        try:
            # Connect to an existing database
            self.connection = psycopg2.connect(user=user,
                                               password=password,
                                               host=host,
                                               port=port,
                                               database=database)
            self.Phone = phone_number

            self.ChannelsReserved = {}
            self.ChannelsTableName = f'channels_{self.Phone}'
            self.AdminsTableName = f'admins_{self.Phone}'

            # Create a cursor to perform database operations
            self.cursor = self.connection.cursor()
            # Print PostgreSQL details
            print("PostgreSQL server information")
            print(self.connection.get_dsn_parameters(), "\n")
            # Executing a SQL query
            self.cursor.execute("SELECT version();")
            # Fetch result
            record = self.cursor.fetchone()
            print("You are connected to - ", record, "\n")
            if not self.fetchOne(f'''SELECT EXISTS (
                           SELECT FROM information_schema.tables 
                           WHERE  table_schema = 'public'
                           AND    table_name   = 'admins_{self.Phone}'
                           );''')[0]:
                print(f"Создаем таблицу admins_{self.Phone}")
                self.execute(
                    f'''CREATE TABLE admins_{self.Phone}(
                    USER_ID           BIGINT    NOT NULL,
                    USERNAME           TEXT); ''')

            if not self.fetchOne(f'''SELECT EXISTS (
                                       SELECT FROM information_schema.tables 
                                       WHERE  table_schema = 'public'
                                       AND    table_name   = 'channels_{self.Phone}'
                                       );''')[0]:
                print(f"Создаем таблицу channels_{self.Phone}")
                self.execute(
                    f'''CREATE TABLE channels_{self.Phone}(
                    CHAT_ID           BIGINT    NOT NULL,
                    USERNAME           TEXT    NOT NULL,
                    LAST_POST_ID           BIGINT    NOT NULL,
                    CHECKED_TIME           BIGINT    DEFAULT    0); ''')
        except (Exception, Error) as error:
            print(f"Error while connecting to PostgreDB {error}", )
            if (self.connection):
                self.cursor.close()
                self.connection.close()
                print("PostgreDB connection is closed")

    def ChannelExists(self, Channel: telethon.tl.types.Channel) -> bool:
        result = self.fetchOne(f"SELECT * FROM {self.ChannelsTableName} WHERE CHAT_ID = {Channel.id}")
        if result is not None:
            return True
        else:
            return False

    def AddChannel(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        self.execute(f'INSERT INTO {self.ChannelsTableName}(CHAT_ID, USERNAME, LAST_POST_ID) VALUES(\'{Channel.id}\', \'{Channel.username}\', \'{LastPostId}\')')

    def DeleteChannel(self, Channel: telethon.tl.types.Channel):
        self.execute(f'DELETE FROM {self.ChannelsTableName} WHERE CHAT_ID = \'{Channel.id}\'')

    def GetChannels(self):
        t10 = int(time.time()) - 10
        t = int(time.time())
        chs = self.fetchAll(f'WITH updated as ('
         f'UPDATE {self.ChannelsTableName} SET checked_time = {t} WHERE (checked_time <= {t10} OR checked_time = 0 OR checked_time IS NULL) RETURNING *)'
         f' SELECT u.*, COUNT(*) OVER () AS total_update_count FROM updated AS u'
        )

        return chs

    def GetAllChannels(self):
        with lock:
            return self.fetchAll(f'SELECT * FROM {self.ChannelsTableName}')

    def UpdateLastPostId(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        self.execute(f'UPDATE {self.ChannelsTableName} SET LAST_POST_ID = {LastPostId} WHERE CHAT_ID = \'{Channel.id}\'')

    def UpdateLastPostIdByInt(self, Channel_id: int, LastPostId: int):
        self.execute(f'UPDATE {self.ChannelsTableName} SET LAST_POST_ID = {LastPostId} WHERE CHAT_ID = \'{Channel_id}\'')

    def IsAdmin(self, User: telethon.tl.types.User) -> bool:
        result = self.fetchOne(f'SELECT * FROM {self.AdminsTableName} WHERE USER_ID = \'{User.id}\'')
        if result is not None:
            return True
        else:
            return False

    def AddAdmin(self, User: telethon.tl.types.User):
        self.execute(f'INSERT INTO {self.AdminsTableName}(USER_ID, USERNAME) VALUES(\'{User.id}\', \'{User.username}\')')

    def DeleteAdmin(self, User: telethon.tl.types.User):
        self.execute(f'DELETE FROM {self.AdminsTableName} WHERE USER_ID = \'{User.id}\'')

    def execute(self, query):
        with lock:
            try:
                self.cursor.execute(query)
                self.connection.commit()
            except (Exception, Error) as error:
                print("Error while connecting to PostgreSQL", error)

    def fetchOne(self, query):
        with lock:
            try:
                self.cursor.execute(query)
                return self.cursor.fetchone()
            except (Exception, Error) as error:
                print(f"Error while fetching query from PostgreDB: {error}")

    def fetchMany(self, query, size):
        with lock:
            try:
                self.cursor.execute(query)
                return self.cursor.fetchmany(size)
            except (Exception, Error) as error:
                print(f"Error while fetching many queries from PostgreDB: {error}")

    def fetchAll(self, query):
        with lock:
            try:
                self.cursor.execute(query)
                return self.cursor.fetchall()
            except (Exception, Error) as error:
                print(f"Error while fetching all queries from PostgreDB: {error}")