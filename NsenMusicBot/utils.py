# coding=utf-8
import subprocess
import urllib.parse
from logging import Logger, Formatter, getLogger, captureWarnings, INFO, DEBUG
from logging.handlers import RotatingFileHandler
from typing import List

from NsenMusicBot.locale.localizer import Localizer

localizer = Localizer()

def decodeURIString(s: str) -> str:
	return urllib.parse.unquote(s)

def executeCommand(args: str) -> List[str]:
	p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = (x.decode() for x in p.communicate())
	return stdout, stderr

def getCustomLogger(logPath: str, debug=False) -> Logger:
	logger = getLogger()
	captureWarnings(capture=True)

	handler = RotatingFileHandler(logPath, maxBytes=2 ** 20, backupCount=10000, encoding="utf-8")
	formatter = Formatter(localizer.get("logFormat"), localizer.get("logTimeFormat"))
	handler.setFormatter(formatter)

	logger.setLevel(DEBUG if debug else INFO)
	logger.addHandler(handler)

	return logger
