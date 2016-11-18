# NsenBot
NsenBotは [Nsen](http://ex.nicovideo.jp/nsenexp/) の放送をDiscordのボイスチャンネルで再生するBotです。
<br>ニコ動のログイン情報とDiscordの`Bot Token`を設定ファイルに記載するだけで使用できます。

## 特徴
### Nsenの再生機能
Nsenで再生されている動画の音声をDiscordのボイスチャンネルで再生します。
<br>Nsenのチャンネルと指定することもでき、コマンドで変更することも可能です。

### コマンド操作可能
NsenBotには最初から便利なコマンドが実装されています。また、コマンドのプレフィックス(`/`や`!`のようなもの)を任意のものに定義することもできます。

以下は NsenBotに実装されているコマンドです。

|コマンド|説明|
|:-----------:|:------------:|
|channel `str`|Nsenのチャンネルを `str` に変更します。`str`には `vocaloid` `toho`などを指定できます。<br>詳しくは`help`コマンドで確認してください。|
|queue|現在の再生キューを取得します。この再生キューは Nsenとの同期ズレが生じるため使用されます。<br>つまり このキューが空でないときは Nsenとの再生時間のズレが発生しています。特にこれは問題ありません。|
|skip|現在の曲をスキップする投票を始めます。|
|volume|現在のプレイヤーの音量を取得します。|
|volume `int`|プレイヤーの音量を `int`% に変更します。|
|volume `[+ または -]int`|プレイヤーの音量を `int`% だけ増加または減少させます。|
|help|ヘルプを表示します。|

## 動作環境
Python 3.5以上 (async-await構文を使用しているため)

## インストール方法
```bash=
cd /path/to/install
git clone https://github.com/SlashNephy/NsenBot

cd NsenBot
pip3 install -r requirements.txt

cp sample.config.json config.json
vi config.json

python3 NsenBot.py
```

## 設定
`sample.config.json`を参考に`config.json`を作成してください。
<br>以下は `sample.config.json`の設定値の一覧です。

|設定値|データ型|説明|例|
|:-----------:|:------------:|:------------:|:------------:|
|tmpDir|str|動画を一時キャッシュするディレクトリを指定します。`NsenBot.py`と同じディレクトリに配置することをおすすめします。|"/path/to/tmp"|
|logDir|str|ログを保管するディレクトリを指定します。`NsenBot.py`と同じディレクトリに配置することをおすすめします。|"/path/to/logs"|
|debug|bool|ログレベルとデバッグにするかどうかです。有効にした場合、ログファイルが肥大化する可能性があります。|false|
|bot|dict|以下に別に示します。|-|
|niconico|dict|以下に別に示します。|-|

<br>次は `sample.config.json`の設定値のうち `bot`以下のものです。

|設定値|データ型|説明|例|
|:-----------:|:------------:|:------------:|:------------:|
|token|str|DiscordのBotのTokenです。<br>Tokenは[ここ](https://discordapp.com/developers/applications/me)で取得できます。|"----------------------------------------"|
|channel|str|デフォルトで接続するボイスチャンネルのIDです。|"248432693862334466"|
|textChannel|str|コマンドの応答や再生中の曲情報をポストするテキストチャンネルのIDです。|"248432693862334464"|
|prefix|str|コマンドの先頭に付け、コマンドを識別する文字です。|"%"|
|needVotes|int|`skip`コマンドでスキップするのに必要な票数です。|3|
|volume|float|1を100%としたデフォルトの音量です。|0.02|
|cleanUpInterval|int|`tmpDir`を掃除する間隔(秒)です。|3600|

<br>次は `sample.config.json`の設定値のうち `niconico`以下のものです。

|設定値|データ型|説明|例|
|:-----------:|:------------:|:------------:|:------------:|
|email|str|ニコ動のアカウント情報のうち、メールアドレスです。|"hoge@example.jp"|
|password|str|ニコ動のアカウント情報のうち、パスワードです。|"foobar114514"|
|default|str|デフォルトで再生するNsenのチャンネルです。詳しくは`help`コマンドをご利用ください。|"toho"|
