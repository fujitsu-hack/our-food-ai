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
from bs4 import BeautifulSoup
import urllib3
import requests
import pathlib
import datetime
import json
import os
import random

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


def create_message(menu_url, user_disp_name):
    r = requests.get(menu_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    elems = soup.find_all("h3", class_="limitTitFloat")
    tmp_food_list = [e.getText() for e in elems]
    msg = "こんにちは " + user_disp_name + " さん!!\n" + \
        "今日の御飯の候補として\n"
    for food in tmp_food_list[0:5]:
        msg = msg + food + "\n"
    msg = msg + "はいかがですか？(^^)\n 作り方は" \
        + menu_url + " を参考にして下さい!!"
    del tmp_food_list
    return msg


def recommend_menu(event):
    # vars
    rakuten_url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426? format=json&categoryType=large&applicationId=1069795497155081416"
    rakuten_res = http.request('GET', rakuten_url)
    rakuten_info = json.loads(rakuten_res.data.decode('utf-8'))
    profile = line_bot_api.get_profile(event.source.user_id)
    num = str(random.randint(1, 4))
    file_name = num + ".jpg"
    image_url = "https://our-food-ai.herokuapp.com/static/" + file_name
    user_disp_name = profile.display_name  # アカウント名

    pred_class = menu_model.pred_class(image_path=image_url)
    menu_url = get_menu_url(rakuten_info, pred_class)
    del rakuten_info
    msg = create_message(menu_url, user_disp_name)
    messages = (ImageSendMessage(original_content_url=FQDN +
                                 "/static/" + file_name, preview_image_url=FQDN + "/static/" + file_name), TextSendMessage(text=msg))

    line_bot_api.reply_message(event.reply_token, messages)


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

    f = pathlib.Path("static/"+user_id+".txt")
    f.touch()
    msg = event.message.text

    if(msg[0:6] == "今日の献立は"):
        recommend_menu(event)

    if(msg[0:6] == "今日のご飯は"):
        with open("static/"+user_id+".txt", "a") as f:
            f.write(datetime.datetime.now().strftime(
                '%Y 年 %m 月 %d 日')+"\n"+msg[6:] + "\n")

    if(msg[0:6] == "過去のご飯は"):
        msg = requests.get(FQDN+"static/"+user_id + ".txt").text
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=msg))


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    user_disp_name = profile.display_name  # アカウント名
    message_content = line_bot_api.get_message_content(event.message.id)

    rakuten_url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426? format=json&categoryType=large&applicationId=1069795497155081416"
    rakuten_res = http.request('GET', rakuten_url)
    rakuten_info = json.loads(rakuten_res.data.decode('utf-8'))
    with open("static/" + event.message.id + ".jpg", "wb") as f:
        f.write(message_content.content)
        image_url = "https://our-food-ai.herokuapp.com/static/" + event.message.id + ".jpg"
        pred_class = menu_model.pred_class(image_path=image_url)
        menu_url = get_menu_url(rakuten_info, pred_class)
        del rakuten_info
        msg = create_message(menu_url, user_disp_name)
        messages = (TextSendMessage(text=msg))
        line_bot_api.reply_message(event.reply_token, messages)


if __name__ == "__main__":
    app.run()
