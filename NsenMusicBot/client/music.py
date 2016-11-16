# coding=utf-8
from .voiceentry import VoiceEntry
from .voicestate import VoiceState

from discord import Channel, ClientException, InvalidArgument
from discord.ext import commands

class Music:
	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}

	def get_voice_state(self, server):
		state = self.voice_states.get(server.id)
		if not state:
			state = VoiceState(self.bot)
			self.voice_states[server.id] = state

		return state

	async def create_voice_client(self, channel):
		voice = await self.bot.join_voice_channel(channel)
		state = self.get_voice_state(channel.server)
		state.voice = voice

	def __unload(self):
		for state in self.voice_states.values():
			try:
				state.audio_player.cancel()
				if state.voice:
					self.bot.loop.create_task(state.voice.disconnect())
			except:
				pass

	@commands.command(pass_context=True, no_pm=True)
	async def join(self, ctx, *, channel: Channel):
		"""Joins a voice channel."""
		try:
			await self.create_voice_client(channel)
		except ClientException:
			await self.bot.say('Already in a voice channel...')
		except InvalidArgument:
			await self.bot.say('This is not a voice channel...')
		else:
			await self.bot.say('Ready to play audio in ' + channel.name)

	@commands.command(pass_context=True, no_pm=True)
	async def summon(self, ctx):
		"""Summons the bot to join your voice channel."""
		summoned_channel = ctx.message.author.voice_channel
		if summoned_channel is None:
			await self.bot.say('You are not in a voice channel.')
			return False

		state = self.get_voice_state(ctx.message.server)
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)

		return True

	@commands.command(pass_context=True, no_pm=True)
	async def play(self, ctx, *, song: str):
		"""Plays a song.
		If there is a song currently in the queue, then it is
		queued until the next song is done playing.
		This command automatically searches as well from YouTube.
		The list of supported sites can be found here:
		https://rg3.github.io/youtube-dl/supportedsites.html
		"""
		state = self.get_voice_state(ctx.message.server)
		opts = {
			'default_search': 'auto',
			'quiet': True,
		}

		if state.voice is None:
			success = await ctx.invoke(self.summon)
			if not success:
				return

		try:
			player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
		except Exception as e:
			fmt = 'An error occurred while processing this request: ```py\n{}: {}\n```'
			await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
		else:
			player.volume = 0.6
			entry = VoiceEntry(ctx.message, player)
			await self.bot.say('Enqueued ' + str(entry))
			await state.songs.put(entry)

	@commands.command(pass_context=True, no_pm=True)
	async def volume(self, ctx, value: int):
		"""Sets the volume of the currently playing song."""

		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.volume = value / 100
			await self.bot.say('Set the volume to {:.0%}'.format(player.volume))

	@commands.command(pass_context=True, no_pm=True)
	async def pause(self, ctx):
		"""Pauses the currently played song."""
		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.pause()

	@commands.command(pass_context=True, no_pm=True)
	async def resume(self, ctx):
		"""Resumes the currently played song."""
		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.resume()

	@commands.command(pass_context=True, no_pm=True)
	async def stop(self, ctx):
		"""Stops playing audio and leaves the voice channel.
		This also clears the queue.
		"""
		state = self.get_voice_state(ctx.message.server)

		if state.is_playing():
			player = state.player
			player.stop()

		try:
			state.audio_player.cancel()
			del self.voice_states[ctx.message.server.id]
			await state.voice.disconnect()
		except:
			pass

	@commands.command(pass_context=True, no_pm=True)
	async def playing(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if not state.current:
			await self.bot.say("Not playing anything.")
		else:
			skip_count = len(state.skip_votes)
			await self.bot.say('Now playing {songTitle} [skips: {voteCount}/3]'.format(songTitle=state.current, voteCount=skip_count))
