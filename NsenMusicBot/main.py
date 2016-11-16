# coding=utf-8
import time
import datetime
import asyncio

import discord

if not discord.opus.is_loaded():
	discord.opus.load_opus("opus")

from NsenMusicBot.utils import getCustomLogger
from NsenMusicBot.nsen import Nsen
from NsenMusicBot.configparser import ConfigParser

class Bot:
	def __init__(self, debug=False):
		configparser = ConfigParser()
		self.config = configparser.config

		self.logger = getCustomLogger("{}/{}.log".format(self.config["logDir"], datetime.datetime.now().strftime("%Y%m%d_%H%M%S")), debug)

		self.bot = discord.Client()
		self.voiceChannel = discord.Object(id=self.config["bot"]["channel"])
		self.textChannel = discord.Object(id=self.config["bot"]["textChannel"])
		self.volume = 0.3

		self.nsen = Nsen(self.config["niconico"]["default"])
		self.nsen.login(self.config["niconico"]["email"], self.config["niconico"]["password"])

		self.tmpDir = self.config["tmpDir"]

		@self.bot.event
		async def on_ready():
			print("Logged in as: {0} (ID: {0.id})".format(self.bot.user))

			await self.playNsen()

	async def playNsen(self):
		voice = await self.bot.join_voice_channel(self.voiceChannel)
		while True:
			try:
				self.nsen.getPlayerStatus()
				duration = int(self.nsen.liveData["stream"]["contents_list"]["contents"]["@duration"])
				text = "Now Playing: {title} ({time}) - {channelName}\n{channelDesc}".format(
						title=self.nsen.liveData["stream"]["contents_list"]["contents"]["@title"],
						time="{}:{:02d}".format(duration / 60, duration % 60),
						channelName=self.nsen.liveData["stream"]["title"],
						channelDesc=self.nsen.liveData["stream"]["description"]
				)
				await self.bot.send_message(self.textChannel, text)
				self.nsen.getCKey()
				self.nsen.getFLV()
				path = "{}.flv".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
				self.nsen.generateCommand(path=path)
				self.nsen.executeRecordCommand()
				player = voice.create_ffmpeg_player(path)
				player.volume = self.volume
				await player.start()
			except:
				self.logger.exception("Error occured while playNsen")
				await asyncio.sleep(10)

	def run(self):
		self.bot.run(self.config["bot"]["token"])
