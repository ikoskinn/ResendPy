import threading
import time

import psycopg2
from psycopg2 import Error

import telethon.tl.types

lock = threading.Lock()


class Postgre:
    connection = None
    cursor = None

    def __init__(self, user, password, host, port, database):
        try:
            # Connect to an existing database
            self.connection = psycopg2.connect(user=user,
                                               password=password,
                                               host=host,
                                               port=port,
                                               database=database)

            self.ChannelsReserved = {}

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
            if not self.fetchOne('''SELECT EXISTS (
                           SELECT FROM information_schema.tables 
                           WHERE  table_schema = 'public'
                           AND    table_name   = 'admins'
                           );''')[0]:
                print("Создаем таблицу Admins")
                self.execute(
                    '''CREATE TABLE Admins(
                    USER_ID           BIGINT    NOT NULL,
                    USERNAME           TEXT); ''')

            if not self.fetchOne('''SELECT EXISTS (
                                       SELECT FROM information_schema.tables 
                                       WHERE  table_schema = 'public'
                                       AND    table_name   = 'channels'
                                       );''')[0]:
                print("Создаем таблицу Channels")
                self.execute(
                    '''CREATE TABLE Channels(
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
        result = self.fetchOne(f"SELECT * FROM Channels WHERE CHAT_ID = {Channel.id}")
        if result is not None:
            return True
        else:
            return False

    def AddChannel(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        self.execute(f'INSERT INTO Channels(CHAT_ID, USERNAME, LAST_POST_ID) VALUES(\'{Channel.id}\', \'{Channel.username}\', \'{LastPostId}\')')

    def DeleteChannel(self, Channel: telethon.tl.types.Channel):
        self.execute(f'DELETE FROM Channels WHERE CHAT_ID = \'{Channel.id}\'')

    def GetUnreservedChannels(self, max = 20):
        chs = self.GetAllChannels()
        channels = {}
        i = 0
        for ch in chs:
            if ch[1] not in self.ChannelsReserved:
                channels[ch[1]] = ch
                self.ChannelsReserved[ch[1]] = ch
                i = i + 1
                if i >= max:
                    break

        return channels

    def UnreserveChannels(self, Channels: dict):
        for ch_username in Channels:
            del self.ChannelsReserved[ch_username]



        # f'WITH updated as ('
        # f'UPDATE Channels SET CHECKED_TIME = \'{dat}\' WHERE CHECKED_TIME <= \'{dat_fwd}\' RETURNING *)'
        # f' SELECT u.*, COUNT(*) OVER () AS total_update_count FROM updated AS u LIMIT {max}'

    def GetAllChannels(self):
        with lock:
            return self.fetchAll(f'SELECT * FROM Channels')

    def UpdateLastPostId(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        self.execute(f'UPDATE Channels SET LAST_POST_ID = {LastPostId} WHERE CHAT_ID = \'{Channel.id}\'')

    def IsAdmin(self, User: telethon.tl.types.User) -> bool:
        result = self.fetchOne(f'SELECT * FROM Admins WHERE USER_ID = \'{User.id}\'')
        if result is not None:
            return True
        else:
            return False

    def AddAdmin(self, User: telethon.tl.types.User):
        self.execute(f'INSERT INTO Admins(USER_ID, USERNAME) VALUES(\'{User.id}\', \'{User.username}\')')

    def DeleteAdmin(self, User: telethon.tl.types.User):
        self.execute(f'DELETE FROM Admins WHERE USER_ID = \'{User.id}\'')

    def execute(self, query):
        try:
            self.cursor.execute(query)
            self.connection.commit()
        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def fetchOne(self, query):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchone()
        except (Exception, Error) as error:
            print(f"Error while fetching query from PostgreDB: {error}")

    def fetchMany(self, query, size):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchmany(size)
        except (Exception, Error) as error:
            print(f"Error while fetching many queries from PostgreDB: {error}")

    def fetchAll(self, query):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except (Exception, Error) as error:
            print(f"Error while fetching all queries from PostgreDB: {error}")
