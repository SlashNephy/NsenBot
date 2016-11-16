# coding=utf-8
from logging import getLogger

from NsenMusicBot.const import configFilename

logger = getLogger()

class ExceptionBase(Exception):
	message = None

	def __init__(self):
		logger.exception(self.message)
		Exception.__init__(self, self.message)

	def __str__(self):
		return self.message

class NotFoundConfigFile(ExceptionBase):
	message = "Config file `{}` is not found.".format(configFilename)

class InvalidSyntaxConfigFile(ExceptionBase):
	message = "Config file `{}` has invalid syntax.".format(configFilename)
