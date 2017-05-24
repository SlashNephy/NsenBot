# coding=utf-8
import subprocess
import urllib.parse
from logging import Logger, Formatter, getLogger, INFO, DEBUG
from logging.handlers import RotatingFileHandler
from typing import Tuple


def encodeURIString(s: str) -> str:
	return urllib.parse.quote(s)

def decodeURIString(s: str) -> str:
	return urllib.parse.unquote(s)

def executeCommand(args: str) -> Tuple[str]:
	p = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = (x.decode() for x in p.communicate())
	return stdout, stderr

def getCustomLogger(logPath: str, debug: bool=False) -> Logger:
	logger = getLogger()

	handler = RotatingFileHandler(logPath, maxBytes=2 ** 20, backupCount=10000, encoding="utf-8")
	formatter = Formatter(
			"[%(asctime)s][%(threadName)s %(name)s/%(levelname)s]: %(message)s",
			"%H:%M:%S"
	)
	handler.setFormatter(formatter)

	logger.setLevel(DEBUG if debug else INFO)
	logger.addHandler(handler)

	return logger
