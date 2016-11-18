# coding=utf-8
import json
from typing import Optional

import lxml.html
import robobrowser
import xmltodict

from .utils import decodeURIString, executeCommand


class Nsen:
	userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2918.0 Safari/537.36"

	baseUrl = "http://live.nicovideo.jp/watch/nsen/"
	flashUrl = "http://live.nicovideo.jp/nicoliveplayer.swf?160530135720"
	flashVer = "WIN 23,0,0,207"

	channelNames = [
		{
			"name": "vocaloid",
			"title": "VOCALOIDチャンネル",
			"alias": ["ch01", "01"]
		},
		{
			"name": "toho",
			"title": "東方チャンネル",
			"alias": ["ch02", "02"]
		},
		{
			"name": "nicoindies",
			"title": "ニコニコインディーズチャンネル",
			"alias": ["ch03", "03"]
		},
		{
			"name": "sing",
			"title": "歌ってみたチャンネル",
			"alias": ["ch04", "04"]
		},
		{
			"name": "play",
			"title": "演奏してみたチャンネル",
			"alias": ["ch05", "05"]
		},
		{
			"name": "pv",
			"title": "PVチャンネル",
			"alias": ["ch06", "06"]
		},
		{
			"name": "hotaru",
			"title": "蛍の光チャンネル",
			"alias": ["ch99", "99"]
		},
		{
			"name": "allgenre",
			"title": "オールジャンルチャンネル",
			"alias": ["ch00", "00"]
		}
	]

	def __init__(self) -> None:
		self.channelName = None
		self.channelId = None

		self.br = None

	def login(self, username: str, password: str) -> None:
		self.br = robobrowser.RoboBrowser(user_agent=self.userAgent)
		self.br.open("https://account.nicovideo.jp/login?site=niconico")

		form = self.br.get_form(id="login_form")
		form["mail_tel"].value = username
		form["password"].value = password
		self.br.submit_form(form)

	def setChannel(self, name: str) -> None:
		if name not in [x["name"] for x in self.channelNames]:
			raise Exception("Unsupported Nsen Channel ({})".format(name))
		self.channelName = name
		self.load()

	def load(self) -> None:
		self.br.open("http://live.nicovideo.jp/callback?next_url=watch%2Fnsen%2F{}".format(self.channelName))
		self.br.open("http://live.nicovideo.jp/watch/nsen/{}".format(self.channelName))

		self.channelId = lxml.html.fromstring(self.br.state.response.text).xpath("/html/head/meta[14]")[0].attrib["content"].split("/")[-1]

	def getPlayerStatus(self) -> dict:
		self.br.open("http://ow.live.nicovideo.jp/api/getplayerstatus?v={}&locale=JP&seat%5Flocale=JP&lang=ja%2Djp".format(self.channelId))
		return json.loads(json.dumps(xmltodict.parse(self.br.state.response.text))).get("getplayerstatus", {})

	@staticmethod
	def getVideoID(playerStatus: dict) -> Optional[str]:
		return playerStatus["stream"]["contents_list"]["contents"]["#text"].replace("smile:", "") if "stream" in playerStatus else None

	def getCKey(self, videoId: str) -> Optional[str]:
		self.br.open("http://ow.live.nicovideo.jp/api/getckey?referer%5Fid={}&id={}&live%5Ftype=nsen".format(self.channelId, videoId))
		return self.br.state.response.text.replace("ckey=", "") if self.br.state.response.text != "ckey=" else None

	def getFLV(self, videoId: str, ckey: str) -> dict:
		self.br.open("http://flapi.nicovideo.jp/api/getflv?as3=1&no%5Fincrement=1&live%5Ftype=nsen&v={}&nsen%5Ftype={}&ckey={}".format(videoId, self.channelName, ckey))
		return {x.split("=")[0]: x.split("=")[1] for x in self.br.state.response.text.split("&")}

	def generateCommand(self, path: str, rtmpUrl: str, fmst: str) -> str:
		return "rtmpdump -l 2 -r {url} -t {url} -a {app} -y {playpath} -s {flashUrl} -p {pageUrl} -f {flashVer} -C S:{fmst[1]} -C S:{fmst[0]} -C S:{playpath} -o {path}".format(
			url=decodeURIString(rtmpUrl).split("?")[0],
			app="/".join(decodeURIString(rtmpUrl).split("?")[0].split("/")[3:]),
			flashUrl=self.flashUrl,
			pageUrl="{}{}".format(self.baseUrl, self.channelName),
			flashVer="\"{}\"".format(self.flashVer),
			playpath=decodeURIString(rtmpUrl).split("?m=")[1],
			fmst=decodeURIString(fmst).split(":"),
			path=path if path else "{}.flv".format(self.channelName)
		)

	@staticmethod
	def executeRecordCommand(command: str) -> tuple:
		return executeCommand(command)
