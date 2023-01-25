import time

import psycopg2
from psycopg2 import Error

import telethon.tl.types


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

            #self.execute('''CREATE TABLE Channels(ID INT PRIMARY KEY     NOT NULL,CHAT_ID           INT    NOT NULL,USERNAME           TEXT    NOT NULL,LAST_POST_ID           INT    NOT NULL,BLOCKED           BOOLEAN); ''')

            #self.execute('''CREATE TABLE Admins(ID INT PRIMARY KEY     NOT NULL,USER_ID           INT    NOT NULL,USERNAME           TEXT); ''')

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

    def GetAndUpdateChannels(self, max = 20):
        dat = int(time.time())
        dat10 = int(time.time())-10
        return self.fetchAll(f'WITH updated as ('
                             f'UPDATE Channels SET CHECKED_TIME = \'{dat}\' WHERE CHECKED_TIME <= \'{dat10}\' RETURNING *)'
                             f' SELECT u.*, COUNT(*) OVER () AS total_update_count FROM updated AS u LIMIT {max}')

    def GetAllChannels(self):
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
