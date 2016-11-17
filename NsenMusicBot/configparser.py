# coding=utf-8
import json
import os

from .const import configFilename
from .exceptions import NotFoundConfigFile, InvalidSyntaxConfigFile


class ConfigParser:
	configPath = "{}".format(configFilename)

	def __init__(self) -> None:
		self.config = None
		self.load()

	def check(self) -> None:
		if not os.path.isfile(self.configPath):
			raise NotFoundConfigFile

		return True

	@property
	def isValid(self) -> bool:
		return self.check()

	def load(self) -> dict:
		if not self.isValid:
			return

		with open(configFilename) as f:
			try:
				self.config = json.load(f)
			except:
				raise InvalidSyntaxConfigFile
		return self.config
