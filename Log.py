import sys
import time

from termcolor import colored, cprint

class Log:
    def __init__(self, count):
        self.count = count
        pass

    def write(self, message):
        sys.stdout.write(message)
        sys.stdout.flush()

    def write_red(self, message):
        message = colored(message, 'red', attrs=['reverse', 'blink'])
        sys.stdout.write(message)
        sys.stdout.flush()

    def update(self, n):
        for i in range(n):
            print("i:", i, sep='', end="\r", flush=True)
            time.sleep(1)