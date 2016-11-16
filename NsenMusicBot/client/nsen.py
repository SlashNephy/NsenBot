# coding=utf-8
import json
import time

import lxml.html
import robobrowser
import xmltodict

from NsenMusicBot.utils import decodeURIString, executeCommand


class Nsen:
	userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2918.0 Safari/537.36"
	nsenSet = ["vocaloid", "toho", "nicoindies", "sing", "play", "pv", "hotaru"]

	def __init__(self, name):
		if name not in self.nsenSet:
			raise Exception("Unsupported Nsen Channel ({})".format(name))
		self.name = name

		self.liveData = {}
		self.liveTitle = None
		self.liveId = None
		self.liveThumb = None
		self.liveDesc = None
		self.ckey = None
		self.flv = {}

		self.br = None

	def login(self, username, password):
		br = robobrowser.RoboBrowser(user_agent=self.userAgent)
		br.open("https://account.nicovideo.jp/login?site=niconico")

		time.sleep(1)

		form = br.get_form(id="login_form")
		form["mail_tel"].value = username
		form["password"].value = password
		br.submit_form(form)

		br.open("http://live.nicovideo.jp/callback?next_url=watch%2Fnsen%2F{}".format(self.name))
		br.open("http://live.nicovideo.jp/watch/nsen/{}".format(self.name))

		t = lxml.html.fromstring(br.state.response.text)
		self.liveId = t.xpath("/html/head/meta[14]")[0].attrib["content"].split("/")[-1]

		self.br = br

	def getPlayerStatus(self):
		self.br.open(
			"http://ow.live.nicovideo.jp/api/getplayerstatus?v={}&locale=JP&seat%5Flocale=JP&lang=ja%2Djp".format(
				self.liveId))
		t = json.loads(json.dumps(xmltodict.parse(self.br.state.response.text)))["getplayerstatus"]

		self.liveData = t
		self.liveTitle = t["stream"]["title"]
		self.liveThumb = t["stream"]["picture_url"]
		self.liveDesc = t["stream"]["description"]

		self.videoId = t["stream"]["contents_list"]["contents"]["#text"].replace("smile:", "")

		return t

	def getCKey(self):
		url = "http://ow.live.nicovideo.jp/api/getckey?referer%5Fid={}&id={}&live%5Ftype=nsen".format(self.liveId, self.videoId)
		self.br.open(url)
		self.ckey = self.br.state.response.text.replace("ckey=", "")
		return self.ckey

	def getFLV(self):
		url = "http://flapi.nicovideo.jp/api/getflv?as3=1&no%5Fincrement=1&live%5Ftype=nsen&v={}&nsen%5Ftype=toho&ckey={}".format(
			self.videoId, self.ckey)
		self.br.open(url)
		self.flv = {x.split("=")[0]: x.split("=")[1] for x in self.br.state.response.text.split("&")}
		return self.flv

	def generateCommand(self, path=None):
		self.command = ["rtmpdump", "-l 2", "-r {}".format(decodeURIString(self.flv["url"]).split("?")[0]),
			"-t {}".format(decodeURIString(self.flv["url"]).split("?")[0]),
			"-a {}".format("/".join(decodeURIString(self.flv["url"]).split("?")[0].split("/")[3:])),
			"-y {}".format(decodeURIString(self.flv["url"]).split("?m=")[1]),
			"-s http://live.nicovideo.jp/nicoliveplayer.swf?160530135720",
			"-p http://live.nicovideo.jp/watch/nsen/{}".format(self.name),
			"-f \"WIN 23,0,0,207\"",
			"-C S:{}".format(decodeURIString(self.flv["fmst"]).split(":")[1]),
			"-C S:{}".format(decodeURIString(self.flv["fmst"]).split(":")[0]),
			"-C S:{}".format(decodeURIString(self.flv["url"]).split("?m=")[1]),
			"-o {}".format(path if path else "{}.flv".format(self.name))]
		return self.command

	def executeRecordCommand(self):
		return executeCommand(self.command)
