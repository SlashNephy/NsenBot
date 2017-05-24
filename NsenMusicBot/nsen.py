# coding=utf-8
import json
import re
import time
from datetime import datetime, timedelta
from typing import Optional

import lxml.html
import requests
import robobrowser
import xmltodict

from .utils import encodeURIString, decodeURIString, executeCommand


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
		self.userId = re.findall("var User = { id: (\d+)", self.br.state.response.text.replace("\n", ""))[0]

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

	def getVideoFLV(self, videoId: str) -> dict:
		self.br.open("http://www.nicovideo.jp/watch/{}".format(videoId))
		self.br.open("http://flapi.nicovideo.jp/api/getflv/{}".format(videoId))
		return {x.split("=")[0]: x.split("=")[1] for x in self.br.state.response.text.split("&")}

	def getVideoInfo(self, videoId: str) -> dict:
		self.br.open("http://ext.nicovideo.jp/api/getthumbinfo/{}".format(videoId))
		return json.loads(json.dumps(xmltodict.parse(self.br.state.response.text))).get("nicovideo_thumb_response", {})

	def getVideoSearchResult(self, query: str) -> dict:
		self.br.open("http://ext.nicovideo.jp/api/search/search/{}?mode=watch&page=1&sort=v&order=d".format(encodeURIString(query)))
		return json.loads(self.br.state.response.text)

	def getThreadKey(self, flv: dict) -> dict:
		self.br.open("http://flapi.nicovideo.jp/api/getthreadkey?thread={}".format(flv["thread_id"]))
		return {y[0]: y[1] for x in self.br.state.response.text.split("&") for y in [x.split("=")]}

	def getWaybackKey(self, flv: dict) -> Optional[str]:
		self.br.open("http://flapi.nicovideo.jp/api/getwaybackkey?thread={}".format(flv["thread_id"]))
		return self.br.state.response.text.replace("waybackkey=", "") if self.br.state.response.text != "ckey=" else None

	def makeCommentRequestXML(self, flv: dict, threadKey: dict) -> str:
		return """<packet>
    <thread thread="%s" version="20061206" res_from="-1000" user_id="%s" threadkey="%s" force_184="%s"/>
    <thread_leaves thread="%s">0-25:200,5000</thread_leaves>
</packet>""" % (flv["thread_id"], self.userId, threadKey["threadkey"], threadKey["force_184"], flv["thread_id"])

	def makeOldCommentRequestXML(self, flv: dict, threadKey: dict, waybackkey: str, delta: timedelta) -> str:
		timestamp = int(time.mktime((datetime.now() - delta).timetuple()))
		return """<packet>
    <thread thread="%s" version="20061206" res_from="-1000" user_id="%s" threadkey="%s" force_184="%s" waybackkey="%s" when="%s"/>
    <thread_leaves thread="%s">0-25:200,5000</thread_leaves>
</packet>""" % (flv["thread_id"], self.userId, threadKey["threadkey"], threadKey["force_184"], waybackkey, timestamp, flv["thread_id"])

	def getVideoComment(self, flv: dict, xml: str) -> list:
		headers = {
			"Content-Type": "application/xml",
			"User-Agent": self.userAgent
		}
		t = requests.post(decodeURIString(flv["ms"]), data=xml, headers=headers)
		t.encoding = t.apparent_encoding

		return sorted([{
			"id": x.get("@user_id"),
			"sec": float(x["@vpos"]) / 100.0 if "@vpos" in x else None,
			'text': x.get("#text")
		} for x in xmltodict.parse(t.text)["packet"]["chat"]], key=lambda x: x["sec"])

	def getNsendata(self) -> dict:
		self.br.open("http://live.nicovideo.jp/nsendata?v={}".format(self.channelId))
		t = json.loads(self.br.state.response.text)
		if "waitlist" not in t:
			return {}
		t2 = lxml.html.fromstring(t["waitlist"])
		t["waitlist"] = [{
			"position": i + 1,
			"icon": x[0][0][0].attrib["src"],
			"url": x[1][0][0].attrib["href"],
			"name": x[1][0][0].text_content()
		} for i, x in enumerate(t2[1]) if len(x) > 0] if len(t2) > 1 else []
		t2 = lxml.html.fromstring(t["history"])
		t["history"] = [{
			"video": {
				"title": x[1][1][0].text_content().strip(),
				"url": x[0][0].attrib["href"],
				"thumb": x[0][0][0].attrib["src"]
			},
			"user": {
				"name": x[1][0].text_content().replace("さんのリクエスト", "").strip(),
				"url": x[1][0][0].attrib["href"] if len(x[1][0]) > 0 else None,
				"official": not len(x[1][0]) > 0
			},
			"good": int(x[1][2].text_content().strip())
		} for x in t2]
		t2 = lxml.html.fromstring(t["playing"])
		t["playing"] = {
			"video": {
				"title": t2[1][1][0].text_content().strip(),
				"url": t2[0][0].attrib["href"],
				"thumb": t2[0][0][0].attrib["src"]
			},
			"user": {
				"name": t2[1][0].text_content().replace("さんのリクエスト", "").strip(),
				"url": t2[1][0][0].attrib["href"] if len(t2[1][0]) > 0 else None,
				"official": not len(t2[1][0]) > 0
			}
		}
		return t

	def getHeartbeat(self) -> dict:
		self.br.open("http://ow.live.nicovideo.jp/api/heartbeat", method="post", data="screen=ScreenNormal&lang=ja%2Djp&v={}&locale=JP&datarate=69285%2E71428571429&seat%5Flocale=JP".format(self.channelId))
		return json.loads(json.dumps(xmltodict.parse(self.br.state.response.text))).get("heartbeat", {})

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
