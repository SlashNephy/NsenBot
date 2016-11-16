# coding=utf-8
import discord
from discord.ext import commands

if not discord.opus.is_loaded():
	discord.opus.load_opus("opus")

from NsenMusicBot.client import Music
from NsenMusicBot.configparser import ConfigParser

class Bot:
	def __init__(self):
		configparser = ConfigParser()
		self.config = configparser.config

		self.bot = commands.Bot(
				command_prefix=commands.when_mentioned_or(self.config["bot"]["prefix"]),
				description="Nsen Music Bot for Discord"
		)
		self.bot.add_cog(Music(self.bot))

		@self.bot.event
		async def on_ready():
			print("Logged in as:\n{0} (ID: {0.id})".format(self.bot.user))

	def run(self):
		self.bot.run(self.config["bot"]["token"])
