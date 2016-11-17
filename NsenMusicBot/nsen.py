# coding=utf-8
from typing import Dict

import lxml.html
import robobrowser
import xmltodict

from .utils import decodeURIString, executeCommand


class Nsen:
	userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2918.0 Safari/537.36"

	baseUrl = "http://live.nicovideo.jp/watch/nsen/"
	flashUrl = "http://live.nicovideo.jp/nicoliveplayer.swf?160530135720"
	flashVer = "WIN 23,0,0,207"

	def __init__(self, name: str) -> None:
		if name not in ["vocaloid", "toho", "nicoindies", "sing", "play", "pv", "hotaru"]:
			raise Exception("Unsupported Nsen Channel ({})".format(name))
		self.channelName = name
		self.channelId = None

		self.br = None

		self.initializeLive()

	def initializeLive(self) -> None:
		self.data = {
			"id": None,
			"live": {},
			"flv": {},
			"ckey": None,
			"command": None
		}

	def login(self, username: str, password: str) -> None:
		br = robobrowser.RoboBrowser(user_agent=self.userAgent)
		br.open("https://account.nicovideo.jp/login?site=niconico")

		form = br.get_form(id="login_form")
		form["mail_tel"].value = username
		form["password"].value = password
		br.submit_form(form)

		br.open("http://live.nicovideo.jp/callback?next_url=watch%2Fnsen%2F{}".format(self.channelName))
		br.open("http://live.nicovideo.jp/watch/nsen/{}".format(self.channelName))

		self.channelId = lxml.html.fromstring(br.state.response.text).xpath("/html/head/meta[14]")[0].attrib["content"].split("/")[-1]

		self.br = br

	def getPlayerStatus(self) -> Dict:
		url = "http://ow.live.nicovideo.jp/api/getplayerstatus?v={}&locale=JP&seat%5Flocale=JP&lang=ja%2Djp".format(self.channelId)
		self.br.open(url)

		t = xmltodict.parse(self.br.state.response.text)["getplayerstatus"]
		self.data["id"] = t["stream"]["contents_list"]["contents"]["#text"].replace("smile:", "")
		self.data["live"] = t

		return t

	def getCKey(self) -> str:
		url = "http://ow.live.nicovideo.jp/api/getckey?referer%5Fid={}&id={}&live%5Ftype=nsen".format(self.channelId, self.data["id"])
		self.br.open(url)

		self.data["ckey"] = self.br.state.response.text.replace("ckey=", "")
		return self.data["ckey"]

	def getFLV(self) -> dict:
		url = "http://flapi.nicovideo.jp/api/getflv?as3=1&no%5Fincrement=1&live%5Ftype=nsen&v={}&nsen%5Ftype={}&ckey={}".format(self.data["id"], self.channelName, self.data["ckey"])
		self.br.open(url)

		self.data["flv"] = {x.split("=")[0]: x.split("=")[1] for x in self.br.state.response.text.split("&")}
		return self.data["flv"]

	def generateCommand(self, path: str=None) -> str:
		self.data["command"] = "rtmpdump -l 2 -r {url} -t {url} -a {app} -y {playpath} -s {flashUrl} -p {pageUrl} -f {flashVer} -C S:{fmst[1]} -C S:{fmst[0]} -C S:{playpath} -o {path}".format(
			url=decodeURIString(self.data["flv"]["url"]).split("?")[0],
			app="/".join(decodeURIString(self.data["flv"]["url"]).split("?")[0].split("/")[3:]),
			flashUrl=self.flashUrl,
			pageUrl="{}{}".format(self.baseUrl, self.channelName),
			flashVer="\"{}\"".format(self.flashVer),
			playpath=decodeURIString(self.data["flv"]["url"]).split("?m=")[1],
			fmst=decodeURIString(self.data["flv"]["fmst"]).split(":"),
			path=path if path else "{}.flv".format(self.channelName)
		)
		return self.data["command"]

	def executeRecordCommand(self) -> tuple:
		return executeCommand(self.data["command"])
