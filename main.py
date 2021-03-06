from flask import Flask, request, abort
import random

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage, StickerMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage, AudioSendMessage, JoinEvent, MemberJoinedEvent
)
import os
import random
import bs4, requests
from pathlib import Path
from PIL import Image

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

name_dict = {}

# 喋った回数
say_counter_dict = {}
count_num = 0

# ユーザがテキストメッセージを送った時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ユーザが入力したメッセージ
    user_message = event.message.text

    # 複数のことを言わせたいときに使う
    msg_list = []
    send_messages = []

    to_silece_person = ["好きな食べ物は何ですか？", "今日の体調はいかがですか？", "好きな野菜は何ですか？", "好きなフルーツは何ですか？"]

    global count_num
    count_num += 1

    # 会話に入ってない人に話しかける
    if count_num >= 30:
        for k, v in say_counter_dict.items():
            # 一番喋っていない人をターゲットにする
            if v == min(say_counter_dict.values()):
                silence = k

        #msg_list.append("オタクくんさぁ...ゲームばっかやってないで会話に参加しようよ!")
        msg_list.append(name_dict[silence] + "さん！あまり喋ってないね？")
        msg_list.append("君も会話に参加しよう！")
        msg_list.append(name_dict[silence] + "さん，" + to_silece_person[random.randint(0, len(to_silece_person) - 1)])

        # メッセージの設定
        for message in msg_list:
            send_messages.append(TextSendMessage(text=message))
        
        # 初期化
        for k in say_counter_dict.keys():
            say_counter_dict[k] = 0
        # 初期化
        count_num = 0
        # メッセージ送信
        line_bot_api.reply_message(
            event.reply_token,
            send_messages
        )
    
    # 会話カウントも同時に行う
    if not event.source.user_id in name_dict.keys():
        name_dict[event.source.user_id] = line_bot_api.get_profile(event.source.user_id).display_name
        say_counter_dict[event.source.user_id] = 1
    else:
        say_counter_dict[event.source.user_id] += 1


    if user_message == "順番":
        message = createOrder()

    elif user_message == "話題":
        message = createRandomMessage() # bot が話題を生成する

    elif user_message == "自己紹介":
        message = createSelfIntroductionMessage()

    elif user_message == "最新ニュース":

        # URL のリストが返ってくる
        msg_list = display_latest_news()
        send_messages = []

        for message in msg_list:
            send_messages.append(TextSendMessage(text=message))
        
        line_bot_api.reply_message(
            event.reply_token,
            send_messages
        )

    # bot を退会させる言葉
    elif user_message == "さよならbot":
        messages = ["そんな...ひどい", "所詮私はその程度の存在だったのね...!", "うわあああん！"]
        send_messages = []

        for message in messages:
            send_messages.append(TextSendMessage(text=message))
        
        line_bot_api.reply_message(event.reply_token, send_messages)
        if hasattr(event.source, "group_id"):
            line_bot_api.leave_group(event.source.group_id)
        return
    
    elif user_message == "bokete":
        # 送信する写真を取得
        message = boketer()
        # テキストと写真を送信する
        send_messages = [TextSendMessage(text="この写真でボケて！"), message]
        line_bot_api.reply_message(
            event.reply_token,
            send_messages
        )
        return
    
    elif user_message.endswith("と呼んで"):
        # 「と呼んで」の部分（後ろ4文字）を削除
        name = user_message[:-4]
        # name_dict にあだ名を登録
        name_dict[event.source.user_id] = name
        # メッセージ作成
        message = "はい，{}さん".format(name)

    elif user_message == "bot":
        message = stamper(event)
        return
    
    # あだ名の一覧を表示
    elif user_message == "あだ名":
        message = getNickname()
    
    # コマンドのヘルプを表示
    elif user_message == "help" or user_message == "ヘルプ":
        message = """かぎかっこの中の言葉を送信すると，botが色々なことをします．
「話題」：話題を生成します．
「自己紹介」：自己紹介で喋る内容を提案します．
「順番」：喋る順番を提案します．
「○○と呼んで」：あだ名を登録します．これ以降botはあなたをあだ名で呼びます．
「bokete」：写真を表示します．ボケてください．
「最新ニュース」：ニュースを5件表示します．
「あだ名」：登録したあだ名の一覧を表示します．
「さよならbot」：botを退会させます．
画像を送信すると，送信された画像を燃やして返します．画像によってはうまく燃えません．"""

    elif user_message == "年齢は？":
        message = "禁則事項です"
    
    elif user_message == "体重は？":
        message = "ひ・み・つ"


    # テキストメッセージを送信
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))


# ユーザが画像を送信したときの処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # メッセージのID
    message_id = event.message.id
    
    # ユーザが送信した画像を保存
    saveImage(message_id)

    # 返す画像のURLが返ってくる
    after_image_url = fireImage(message_id)

    # 画像を返す
    line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url = after_image_url,
                preview_image_url = after_image_url
            ))


# botがグループに参加したときの処理
@handler.add(JoinEvent)
def handle_join(event):
    # 送信するメッセージ
    message = "招待ありがとう！\nみんな自己紹介してね！\n詳しい使い方を表示するには「help」または「ヘルプ」と入力してください．"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )


# 新しくユーザが参加したときの処理
@handler.add(MemberJoinedEvent)
def handle_member_join(event):

    # 新しく入ったメンバーのIDを取得
    new_user_id = event.joined.members[0].user_id
    # ユーザのプロフィールを取得
    profile = line_bot_api.get_profile(new_user_id)
    # ディスプレイネーム取得
    disp_name = profile.display_name
    # 送るメッセージ
    message = "いらっしゃい" + disp_name + "さん！\nさあ，自己紹介をするんだ！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

# 順番を作る
def createOrder():
    message = ""
    id_list = list(name_dict.keys())
    random.shuffle(id_list)

    for i in range(len(id_list)):
        message += name_dict[id_list[i]]
        message += ' : ' + str(i + 1)
        if i == len(id_list) - 1:
            pass
        else:
            message += "\n"
    return message

# 話題を作成
def createRandomMessage():
    # メッセージ
    message = ""

    # 誰の
    who = ["あなた", "友人", "先輩", "家族", "兄弟", "後輩"]

    # いつ
    when = ["昨日", "一昨日", "先週", "先月", "半年くらい前", "去年", "高校時代", "中学時代", "小学生時代", "子供時代"]

    # どんな話
    what = ["笑える", "泣ける", "悲しい", "すべらない", "どうでもいい", "気になる", "ためになる", "ショックな", "ビッグな", "情けない", "怖い", "恋の", "恥ずかしい"]

    # メッセージ作成
    # 誰のいつのどんな話
    message = "{}の{}の{}話".format(who[random.randint(0, len(who) - 1)], when[random.randint(0, len(when) - 1)], what[random.randint(0, len(what) - 1)])

    return message


# 自己紹介の内容を作成
def createSelfIntroductionMessage():
    # メッセージ
    message = "名前は？\nあだ名は？"

    # 普通な話題
    wadai = ["出身は？", "趣味は？", "部活について", "これからやりたいことは？", "好きな食べ物は？", "誕生日は？"]

    # 九工大特化な話題
    wadai_kyutech = ["twitterやってる？", "好きなアニメは？", "視力は？", "好きなゲームは？", "受験の選択科目は？", "何類？何クラス？"]

    # メッセージ作成
    message += "\n" + wadai[random.randint(0, len(wadai) - 1)] + "\n" + wadai_kyutech[random.randint(0, len(wadai_kyutech) - 1)]

    return message

# boketeの画像を送信
def boketer():
    image_url = "https://icebreaker2020.herokuapp.com/static/images/no" + str(random.randint(1,12)) + ".jpg"
    message = ImageSendMessage(
        original_content_url = image_url,
        preview_image_url = image_url
        )
    return message

# 最近のニュースの URL のリストを返す
def display_latest_news():
    # 返す URL のリスト
    msg_list = []

    # ヤフーニュースから取ってくる
    result = requests.get("https://news.yahoo.co.jp/")
    # 接続確認
    result.raise_for_status()
    # HTML で扱えるようにする？
    soup = bs4.BeautifulSoup(result.text, "html.parser")
    # リンクの要素
    link_element = soup.select(".topicsListItem > a")
    # URL を返す
    for i in range(5):
        msg_list.append(link_element[i].get("href"))

    return msg_list

# スタンプを送信
def stamper(event):
    randnum = random.randint(1,100)
    msg_list = []
    msg_list.append(TextSendMessage(text="運試しのようなもの\n100分の1の確率で激レアスタンプだ！"))

    if randnum == 1:
        msg_list.append(TextSendMessage(text="激レアスタンプ！"))
        msg_list.append(StickerSendMessage(
            package_id = 1,
            sticker_id = 2
        ))
        msg_list.append(TextSendMessage(text="おめでとう！"))
    else:
        msg_list.append(StickerSendMessage(
            package_id = 1,
            sticker_id = 1
        ))
        msg_list.append(TextSendMessage(text="はずれ"))
    
    line_bot_api.reply_message(
        event.reply_token,
        msg_list
    )

    return


# 登録したあだ名を返す
def getNickname():
    id_list = list(name_dict.keys())
    message = ""
    for i in range(len(id_list)):
        message += line_bot_api.get_profile(id_list[i]).display_name
        message += " : "
        message += name_dict[id_list[i]]
        if i == len(id_list) - 1:
            pass
        else:
            message += "\n"
    return message

# 画像を保存する
def saveImage(message_id):
    # 画像ファイルの絶対パス
    path_to_image = Path("static/userSendImages/{}.jpg".format(message_id)).absolute()

    # ディレクトリが存在しなければ作成
    os.makedirs(os.path.join("static", "userSendImages"), exist_ok=True)

    # 画像のバイナリデータを取得
    message_content = line_bot_api.get_message_content(message_id)
    with open(path_to_image, "wb") as f:
        # バイナリを1024バイトずつ書き込む
        for chunk in message_content.iter_content():
            f.write(chunk)

# 画像を加工する
def fireImage(message_id):
    # 背景画像を開く
    bg_im = Image.open("static/bg_fire_trimed_touka.png")
    # ユーザが送信した写真を開く
    im = Image.open("static/userSendImages/{}.jpg".format(message_id))
    # それを縮小
    im.thumbnail((640, 640))
    # 重ねる
    im.paste(bg_im, (0, 0), bg_im)
    # 保存
    im.save("static/userSendImages/after{}.jpg".format(message_id))
    # 返す画像のURL
    return "https://icebreaker2020.herokuapp.com/static/userSendImages/after{}.jpg".format(message_id)


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



