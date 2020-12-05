#!/usr/bin/env python3
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
)
from model.menu_model import MenuModel

import requests
import json
import urllib3
import os

# image
from PIL import Image 

dirname = os.getcwd()
model_path = dirname + "/model/model_006_0.1673.h5"
menu_model = MenuModel(model_path)

app = Flask(__name__)
http = urllib3.PoolManager()

access_token = "i8mVu+Jb36emJ0wI3zT+3HtnRMapNIqRxGucYmsGOnfiUGZ8ea7donXDANqxEMQSVpkfTgWxNylTjXNiAqqp0iAp1Pn4jB8vnWOfqK9SKPoWMiTrA9xGjy826ELQ1BN1EV34s8itM7xgoI8cP1jkzAdB04t89/1O/w1cDnyilFU="
secret_key = "92a9f9a66c41ca94624822c4ad3df774"
line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret_key)

FQDN = "https://our-food-ai.herokuapp.com/"
http = urllib3.PoolManager()


def get_menu_url(rakuten_info, pred_class):
    if pred_class == 0:
        class_name = "定番の肉料理"
    elif pred_class == 1:
        class_name = "定番の魚料理"
    elif pred_class == 2:
        class_name = "鍋料理"
    elif pred_class == 3:
        class_name = "サラダ"
    else:
        print("No value is assigned to pred_class.")

    key = rakuten_info["result"]["large"]
    for _, large in enumerate(key):
        if large["categoryName"] == class_name:
            menu_url = large["categoryUrl"]
            return menu_url


@app.route("/receiveImage", methods=["POST", "GET"])
def receive_image():
    print("\n\nrequest\n\n", request)
    img = Image.open(request.files['upfile'])

    img.save("./static/sample.jpg")
    print("\n\ndata: {}\n\n".format(""))
    return "success"






@app.route("/")
def hello_world():
    return "hello world!"


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    user_id = event.source.user_id  # ユーザ ID (zzz)
    user_disp_name = profile.display_name  # アカウント名
    msg = "送り主は" + user_disp_name + "です"
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=msg))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    user_disp_name = profile.display_name  # アカウント名
    message_content = line_bot_api.get_message_content(event.message.id)

    ####### ここを書いてください #######
    rakuten_url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426? format=json&categoryType=large&applicationId=1069795497155081416"
    ##############################

    rakuten_res = http.request('GET', rakuten_url)
    rakuten_info = json.loads(rakuten_res.data.decode('utf-8'))

    with open("static/" + event.message.id + ".jpg", "wb") as f:
        f.write(message_content.content)
        image_url = "https://our-food-ai.herokuapp.com/static/" + event.message.id + ".jpg"
        pred_class = menu_model.pred_class(image_path=image_url)
        menu_url = get_menu_url(rakuten_info, pred_class)
        msg = "送り主は" + user_disp_name + "です。\n" + "URL は" + menu_url

        messages = (TextSendMessage(text=msg),
                    ImageSendMessage(original_content_url=FQDN + "/static/" + event.message.id + ".jpg", preview_image_url=FQDN + "/static/" + event.message.id + "jpg"))
        line_bot_api.reply_message(event.reply_token, messages)


if __name__ == "__main__":
    app.run()
