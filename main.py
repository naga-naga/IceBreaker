from flask import Flask, request, abort
import random

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, VideoSendMessage, StickerSendMessage, AudioSendMessage
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

user_list = [] # しゃべったユーザ
num_list = [0]  # 割り当てた番号

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # 送信するメッセージ
    message = ""

    # ユーザが入力したメッセージ
    user_message = event.message.text

    if not event.source.user_id in user_list:
        user_list.append(event.source.user_id)
    
    if user_message == "順番":
        message = createOrder()
        
    elif user_message == "話題":
        #message = event.message.text
        #profile = line_bot_api.get_profile(event.source.user_id)
        #message = profile.display_name
        message = createRandomMessage() # bot が話題を生成する
    elif user_message == "自己紹介":
        message = createSelfIntroductionMessage()
    
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))

def createOrder():
    message = ""
    random.shuffle(user_list)
        num = 0
        for id in user_list:
            num += 1
            profile = line_bot_api.get_profile(id)
            message += profile.display_name
            message += ' : ' + str(num)
            if num == len(user_list):
                pass
            else:
                message += "\n"

# 話題を作成
def createRandomMessage():
    # メッセージ
    message = ""

    # 誰の
    who = ["私", "友人", "先輩", "家族", "兄弟", "後輩"]

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
    message = "名前は？"

    # 普通な話題
    wadai = ["出身は？", "趣味は？", "部活について", "これからやりたいことは？", "あだ名は？", "好きな食べ物は？", "誕生日は？"]

    # 九工大特化な話題
    wadai_kyutech = ["twitterやってる？", "好きなアニメは？", "視力は？", "好きなゲームは？", "受験の選択科目は？", "何類？何クラス？"]

    # メッセージ作成
    message += "\n" + wadai[random.randint(0, len(wadai) - 1)] + "\n" + wadai_kyutech[random.randint(0, len(wadai_kyutech) - 1)]

    return message


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
