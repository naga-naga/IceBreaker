from flask import Flask, request, abort
import random

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage, AudioSendMessage, JoinEvent, MemberJoinedEvent
)
import os
import random

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

#user_list = [] # しゃべったユーザ
name_dict = {}

# ユーザがテキストメッセージを送った時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # ユーザが入力したメッセージ
    user_message = event.message.text

    """
    if not event.source.user_id in user_list:
        user_list.append(event.source.user_id)
    """
    
    if not event.source.user_id in name_dict.keys():
        name_dict[event.source.user_id] = line_bot_api.get_profile(event.source.user_id).display_name
    
    if user_message == "順番":
        message = createOrder()

    elif user_message == "話題":
        message = createRandomMessage() # bot が話題を生成する

    elif user_message == "自己紹介":
        message = createSelfIntroductionMessage()
    elif user_message == "最新ニュース":
        message = display_latest_news()

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
        # 「と呼んで」の部分を削除
        message = user_message.strip("と呼んで")
        # name_dict にあだ名を登録
        name_dict[event.source.user_id] = message
    
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))

# botがグループに参加したときの処理
@handler.add(JoinEvent)
def handle_join(event):
    # 送信するメッセージ
    message = "招待ありがとう！\nみんな自己紹介してね！"

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
    #random.shuffle(user_list)
    id_list = name_dict.keys()
    random.shuffle(id_list)
    return str(id_list[0])

    for i in range(len(id_list)):
        #profile = line_bot_api.get_profile(id)
        #message += profile.display_name
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
def display_latest_news():
    message = "https://news.yahoo.co.jp/pickup/6352292"
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
