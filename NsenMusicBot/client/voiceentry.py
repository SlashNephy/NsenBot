# coding=utf-8

class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

	def __str__(self):
		fmt = "*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}"
		duration = self.player.duration
		if duration:
			fmt += " [length: {0[0]}m {0[1]}s]".format(divmod(duration, 60))
		return fmt.format(self.player, self.requester)
