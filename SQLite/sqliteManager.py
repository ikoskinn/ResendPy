import sqlite3
import threading
import time
from os.path import exists
import telethon.tl.types

lock = threading.Lock()
lockget = threading.Lock()
lockCount = threading.Lock()

class SQLite:
    con = None
    cur = None

    def __init__(self, dbName):
        self.con = sqlite3.connect(f'{dbName}.db', check_same_thread=False)
        self.cur = self.con.cursor()
        try:
            self.cur.execute("CREATE TABLE Channels (chat_id INTEGER, username TEXT, last_post_id INTEGER)")
            self.cur.execute("CREATE TABLE Admins (user_id INTEGER, username TEXT)")
        except:
            pass

    def ChannelExists(self, Channel: telethon.tl.types.Channel) -> bool:
        with lockget:
            try:
                result = self.executeFetchOne(f"SELECT * FROM Channels WHERE chat_id = {Channel.id}")
                if result is not None:
                    return True
                else:
                    return False
            except Exception as e:
                print(e)
                return False
    def AddChannel(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        with lockget:
            try:
                self.execute(f'INSERT INTO Channels VALUES(\'{Channel.id}\', \'{Channel.username}\', \'{LastPostId}\')')
            except Exception as e:
                print(e)
                return None
    def DeleteChannel(self, Channel: telethon.tl.types.Channel):
        with lockget:
            try:
                self.execute(f'DELETE FROM Channels WHERE chat_id = \'{Channel.id}\'')
            except Exception as e:
                print(e)
                return None
    def GetAllChannels(self):
        with lockget:
            try:
                return self.executeFetchAll(f'SELECT * FROM Channels')
            except Exception as e:
                print(e)
                return None
    def UpdateLastPostId(self, Channel: telethon.tl.types.Channel, LastPostId: int):
        with lockget:
            try:
                self.execute(f'UPDATE Channels SET last_post_id = {LastPostId} WHERE chat_id = \'{Channel.id}\'')
            except Exception as e:
                print(e)
                return None

    def IsAdmin(self, User: telethon.tl.types.User) -> bool:
        with lockget:
            try:
                result = self.executeFetchOne(f'SELECT * FROM Admins WHERE user_id = \'{User.id}\'')
                if result is not None:
                    return True
                else:
                    return False
            except Exception as e:
                print(e)
                return False
    def AddAdmin(self, User: telethon.tl.types.User):
        with lockget:
            try:
                self.execute(f'INSERT INTO Admins VALUES(\'{User.id}\', \'{User.username}\')')
            except Exception as e:
                print(e)
                return None
    def DeleteAdmin(self, User: telethon.tl.types.User):
        with lockget:
            try:
                self.execute(f'DELETE FROM Admins WHERE user_id = \'{User.id}\'')
            except Exception as e:
                print(e)
                return None


    def execute(self, cmd):
        with lock:
            try:
                execResult = self.cur.execute(f'{cmd}')
                self.con.commit()
                print(f'Выполнили команду: {cmd}..')
                return execResult
            except Exception as e:
                print(f'Не смогли выполнить команду: {cmd}!')
                print(f'Ошибка: {str(e)}!')
                time.sleep(5)
    def executeFetchAll(self, cmd):
        with lock:
            try:
                print(f'Выполняем команду: {cmd}..')
                execResult = self.cur.execute(f'{cmd}')
                self.con.commit()
                return execResult.fetchall()
            except Exception as e:
                print(str(e))
                pass
    def executeFetchOne(self, cmd):
        with lock:
            try:
                print(f'Выполняем команду: {cmd}..')
                execResult = self.cur.execute(f'{cmd}')
                self.con.commit()
                return execResult.fetchone()
            except Exception as e:
                print(str(e))
                pass