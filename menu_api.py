from flask import *
import requests
import json
import urllib3
import os

from model.menu_model import MenuModel

dirname = os.getcwd()
model_path = dirname + "/model/model_006_0.1673.h5"
menu_model = MenuModel(model_path)

app = Flask(__name__)
http = urllib3.PoolManager()


@app.route("ここを書いてください")
def menu_model():
    ####### ここを書いてください #######
    rakuten_url = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426? format=json&categoryType=large&applicationId=8da348a47531325b1c685f27298319a1"
    ##############################

    rakuten_res = http.request('GET', rakuten_url)
    rakuten_info = json.loads(rakuten_res.data.decode('utf-8'))

    ####### ここを書いてください #######
    image_url = 'http://api:3000/risks'
    ##############################

    pred_class = menu_model.pred_class(image_url=image_url)
    menu_url = get_menu_url(rakuten_info, pred_class)
    return {"menu_url": menu_url}


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
        if large["categoryName"] == class_name
        return menu_url = large["categoryUrl"]


if __name__ == "__main__":
    app.run(debug=True)
