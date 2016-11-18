# coding=utf-8
import asyncio
import datetime
import re
import os
import threading
import time

import discord

from .configparser import ConfigParser
from .nsen import Nsen
from .utils import getCustomLogger


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
		self.player = None
		self._volume = self.config["bot"]["volume"]
		self.nsenChannel = self.config["niconico"]["default"]
		self.voiceChannel = discord.Object(id=self.config["bot"]["channel"])
		self.textChannel = discord.Object(id=self.config["bot"]["textChannel"])
		self.prefix = self.config["bot"]["prefix"]

		self.nsenThread = threading.Thread(name="Sync Nsen Song", target=self.syncNsen)
		self.nsenThread.setDaemon(True)
		self.musicQueue = []
		self.currentVote = []
		self.needVotes = self.config["bot"]["needVotes"]
		self.currentVideoPath = None

		self.nsen = Nsen()
		self.nsen.login(self.config["niconico"]["email"], self.config["niconico"]["password"])
		self.nsen.setChannel(self.nsenChannel)

		self.tmpDir = self.config["tmpDir"]
		self.cleanUpInterval = self.config["bot"]["cleanUpInterval"]
		self.cleanUpThread = threading.Thread(name="Cleaning Up Tmp Dir", target=self.cleanUpTmpDir)

		@self.client.event
		async def on_ready():
			self.logger.info("Logged in as: {0} (ID: {0.id})".format(self.client.user))

			self.voiceClient = await self.client.join_voice_channel(self.voiceChannel)
			await self.loopTrack()

		@self.client.event
		async def on_message(message):
			if message.author == self.client.user:
				return

			def getRegex(command, content):
				m = re.match("^.{} (.+)$".format(command), content)
				return m.group(1) if m else None

			if message.content.startswith(self.prefix + "channel"):
				result = getRegex("channel", message.content)
				if result:
					if result not in [x["name"] for x in self.nsen.channelNames] + [y for x in self.nsen.channelNames for y in x["alias"]]:
						await self.client.send_message(self.textChannel, "{} 与えられたチャンネル **{}** は不正です。詳しくは`help`コマンドをご利用ください。".format(message.author.mention, result))
						return True

					if result in [y for x in self.nsen.channelNames for y in x["alias"]]:
						result = [x["name"] for x in self.nsen.channelNames if result in x["alias"]][0]
					self.nsenChannel = result
					self.musicQueue = []
					self.nsen.setChannel(self.nsenChannel)
					self.player.stop()
					await self.client.send_message(self.textChannel, "{} 再生キューを初期化し、チャンネルを **{}** に変更します。".format(message.author.mention, self.nsenChannel))
					return True

			elif message.content.startswith(self.prefix + "queue"):
				if self.musicQueue:
					await self.client.send_message(self.textChannel, "{} 現在の再生キューです。\n\n{}".format(message.author.mention, "\n".join(["{}. {}".format(i + 1, t["title"]) for i, t in enumerate(self.musicQueue)])))
				else:
					await self.client.send_message(self.textChannel, "{} 現在の再生キューは空です。".format(message.author.mention))
				return True

			elif message.content.startswith(self.prefix + "skip"):
				if self.musicQueue:
					if message.author.id in self.currentVote:
						await self.client.send_message(self.textChannel, "{} すでにスキップ投票をしているため、もう投票できません。".format(message.author.mention))
					else:
						self.currentVote.append(message.author.id)
						if len(self.currentVote) >= self.needVotes:
							self.player.stop()
							await self.client.send_message(self.textChannel, "{} {}票の投票が得られたため、現在の曲をスキップします。".format(message.author.mention, self.needVotes))
						else:
							await self.client.send_message(self.textChannel, "{} スキップ投票を受け付けました。".format(message.author.mention, self.needVotes))

				else:
					await self.client.send_message(self.textChannel, "{} 現在の再生キューは空であるため、スキップできません。".format(message.author.mention))
				return True

			elif message.content.startswith(self.prefix + "volume"):
				result = getRegex("volume", message.content)
				if result and result != 0:
					if result.isdigit():
						self.volume = round(int(result) / 100, 2)
						await self.client.send_message(self.textChannel, "{} 音量を {}% に変更しました。".format(message.author.mention, int(self.volume * 100)))
						return True
					elif result.startswith("+") or result.startswith("-"):
						sign = result[0]
						value = int(result[1:]) if result[1:].isdigit() else None
						if value:
							value = round((1 if sign == "+" else -1) * value / 100, 2)
							if self.volume > value:
								self.volume += value
								await self.client.send_message(self.textChannel, "{} 音量を {}% に変更しました。".format(message.author.mention, int(self.volume * 100)))
								return True
				await self.client.send_message(self.textChannel, "{} 現在の音量は {}% です。".format(message.author.mention, int(self.volume * 100)))
				return True

			if message.content.startswith(self.prefix):
				helps = [
					["channel [str]", "Nsenチャンネルを [str] に変更します。変更可能なチャンネルは {} です。".format(", ".join(["{} ({})".format(x["name"], ", ".join(x["alias"])) for x in self.nsen.channelNames]))],
					["queue", "現在の再生キューを返します。"],
					["volume", "現在の音量を返します。"],
					["volume [int]", "音量を [int]% に変更します。"],
					["volume [+ または -][int]", "音量を [int]% だけ増加または減少させます。"]
				]
				await self.client.send_message(
						self.textChannel,
						"{} Nsen Music Botコマンド一覧:\n\n"
						"```\n"
						"{}"
						"\n\n```".format(
								message.author.mention,
								"\n\n".join(["{0}{1[0]}\n  {1[1]}".format(self.prefix, data) for data in helps])
						)
				)

	@property
	def volume(self):
		return self._volume

	@volume.setter
	def volume(self, value):
		self._volume = value
		if self.player:
			if self.player.is_playing():
				self.player.volume = self._volume

	async def loopTrack(self):
		while self.running:
			await self.goNextTrack()

	async def goNextTrack(self):
		while True:
			track = await self.getTrack()
			try:
				await self.client.send_typing(self.textChannel)

				self.player = self.voiceClient.create_ffmpeg_player(track["path"], use_avconv=True)
				self.player.volume = self.volume
				self.player.start()
				self.currentVote = []

				await self.client.purge_from(self.textChannel, limit=50, check=lambda x: x.author == self.client.user)

				await self.client.send_message(self.textChannel, track["text"])
				await self.client.change_presence(game=discord.Game(name=track["title"]))
				self.logger.info(track["text"])

				while True:
					await asyncio.sleep(1)
					if self.player.is_done():
						await self.client.change_presence(game=None)
						break

			except:
				self.logger.exception("Error occured while goNextTrack")
				await asyncio.sleep(10)

	async def getTrack(self):
		while len(self.musicQueue) == 0:
			await asyncio.sleep(1)
		t = self.musicQueue.pop(0)
		self.currentVideoPath = t["path"]
		return t

	def syncNsen(self):
		previousId = None
		while True:
			try:
				data = self.nsen.getPlayerStatus()
				if "error" in data:
					self.nsen.setChannel(self.nsenChannel)
					time.sleep(10)
					continue
				videoId = self.nsen.getVideoID(data)
				if videoId == previousId:
					time.sleep(10)
					continue
				ckey = self.nsen.getCKey(videoId)
				data2 = self.nsen.getFLV(videoId, ckey)

				duration = int(data["stream"]["contents_list"]["contents"]["@duration"])
				obj = {
					"path": "{}/{}_{}.flv".format(self.tmpDir, self.nsen.channelName, videoId),
					"text": "Now Playing: **{title}** ({time}) - {channelName}\nhttp://www.nicovideo.jp/watch/{id}".format(
						title=data["stream"]["contents_list"]["contents"]["@title"],
						time="{0[0]}:{0[1]:02d}".format(divmod(duration, 60)),
						channelName=data["stream"]["title"],
						id=videoId
					),
					"title": data["stream"]["contents_list"]["contents"]["@title"]
				}
				previousId = videoId

				if not os.path.isfile(obj["path"]):
					command = self.nsen.generateCommand(obj["path"], data2["url"], data2["fmst"])
					result = self.nsen.executeRecordCommand(command)
					self.logger.info("Record Command Result =\n{}\n".format(result))
				self.musicQueue.append(obj)
			except:
				self.logger.exception("Error occured while syncNsen")
				time.sleep(10)

	def cleanUpTmpDir(self):
		while True:
			time.sleep(self.cleanUpInterval)

			for x in os.listdir(self.tmpDir):
				path = "{}/{}".format(self.tmpDir, x)
				if path != self.currentVideoPath:
					os.remove(path)

	def run(self):
		self.running = True

		self.nsenThread.start()
		self.cleanUpThread.start()
		self.client.run(self.config["bot"]["token"])
