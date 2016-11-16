# coding=utf-8
import asyncio

class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
		self.skip_votes = set()
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def is_playing(self):
		if not self.voice or not self.current:
			return False
		return not self.current.player.is_done()

	@property
	def player(self):
		return self.current.player

	def skip(self):
		self.skip_votes.clear()
		if self.is_playing():
			self.player.stop()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def audio_player_task(self):
		while True:
			self.play_next_song.clear()
			self.current = await self.songs.get()
			await self.bot.send_message(self.current.channel, "Now playing {}".format(self.current))
			self.current.player.start()
			await self.play_next_song.wait()
