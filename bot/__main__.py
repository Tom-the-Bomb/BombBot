"""
Program Entry Point, runs the bot
"""
from .bot import BombBot

if __name__ == '__main__':
    bot = BombBot()
    bot.run()