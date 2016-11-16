# coding=utf-8
from NsenMusicBot.locale import en, ja
from NsenMusicBot.configparser import ConfigParser

currentLocale = ConfigParser().config["locale"]
locales = {
	"en": en,
	"ja": ja
}

class Localizer:
	@staticmethod
	def get(name):
		getattr(locales[currentLocale], name)
