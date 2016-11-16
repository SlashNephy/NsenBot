# coding=utf-8
import json
import os

from NsenMusicBot.const import configFilename
from NsenMusicBot.exceptions import NotFoundConfigFile, InvalidSyntaxConfigFile


class ConfigParser:
	configPath = "{}".format(configFilename)

	def __init__(self):
		self.config = None
		self.load()

	def check(self):
		if not os.path.isfile(self.configPath):
			raise NotFoundConfigFile

		return True

	@property
	def isValid(self):
		return self.check()

	def load(self):
		if not self.isValid:
			return

		with open(configFilename) as f:
			try:
				self.config = json.load(f)
			except:
				raise InvalidSyntaxConfigFile
