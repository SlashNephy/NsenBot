# coding=utf-8
import asyncio
import datetime
import time
import threading

import discord

from .utils import getCustomLogger
from .nsen import Nsen
from .configparser import ConfigParser

class Bot:
	def __init__(self):
		self.running = False

		if not discord.opus.is_loaded():
			discord.opus.load_opus("opus")

		self.config = ConfigParser().config

		self.isDebugMode = self.config.get("debug", False)
		self.logger = getCustomLogger("{}/{}.log".format(self.config["logDir"], datetime.datetime.now().strftime("%Y%m%d_%H%M%S")), self.isDebugMode)

		self.client = discord.Client()
		self.voiceClient = None
		self.volume = 0.05
		self.voiceChannel = discord.Object(id=self.config["bot"]["channel"])
		self.textChannel = discord.Object(id=self.config["bot"]["textChannel"])

		self.nsenThread = threading.Thread(name="Sync Nsen Song", target=self.syncNsen)
		self.nsenThread.setDaemon(True)
		self.musicQueue = []

		self.nsen = Nsen(self.config["niconico"]["default"])
		self.nsen.login(self.config["niconico"]["email"], self.config["niconico"]["password"])

		@self.client.event
		async def on_ready():
			self.logger.info("Logged in as: {0} (ID: {0.id})".format(self.client.user))

			self.voiceClient = await self.client.join_voice_channel(self.voiceChannel)
			await self.loopTrack()

	async def loopTrack(self):
		while self.running:
			await self.goNextTrack()

	async def goNextTrack(self):
		track = await self.getTrack()
		try:
			player = self.voiceClient.create_ffmpeg_player(track["path"], use_avconv=True)
			player.volume = self.volume
			player.start()

			await self.client.send_message(self.textChannel, track["text"])
			self.logger.info(track["text"])

			n = 1
			while True:
				self.logger.debug("Sleeping {} secs".format(n))
				await asyncio.sleep(1)
				n += 1
				if player.is_done():
					self.logger.debug("Sleeping is done.")
					break

			self.logger.debug("Current song is done.")
			await self.goNextTrack()
		except:
			self.logger.exception("Error occured while goNextTrack")
			await asyncio.sleep(10)

	async def getTrack(self):
		while len(self.musicQueue) == 0:
			await asyncio.sleep(1)
		return self.musicQueue.pop(0)

	def syncNsen(self):
		previousId = None
		while True:
			try:
				self.nsen.getPlayerStatus()
				while previousId == self.nsen.data["id"]:
					time.sleep(1)
				self.nsen.getCKey()
				self.nsen.getFLV()

				duration = int(self.nsen.data["live"]["stream"]["contents_list"]["contents"]["@duration"])
				obj = {
					"path": "{}/{}.flv".format(self.config["tmpDir"], datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
					"text": "Now Playing: {title} ({time}) - {channelName}".format(
						title=self.nsen.data["live"]["stream"]["contents_list"]["contents"]["@title"],
						time="{0[0]}:{0[1]:02d}".format(divmod(duration, 60)),
						channelName=self.nsen.data["live"]["stream"]["title"]
					)
				}
				previousId = self.nsen.data["id"]

				self.nsen.generateCommand(path=obj["path"])
				result = self.nsen.executeRecordCommand()
				self.logger.info("Record command result =\n{0[0]}\n\nError =\n{0[1]}".format(result[0]))
				self.musicQueue.append(obj)
			except:
				self.logger.exception("Error occured while syncNsen")
				time.sleep(5)
			finally:
				self.nsen.initializeLive()

	def run(self):
		self.running = True

		self.nsenThread.start()
		self.client.run(self.config["bot"]["token"])
