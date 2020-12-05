#!/usr/bin/env python3
import numpy as np
import requests
from PIL import Image
import tensorflow as tf
import io


class MenuModel():
    def __init__(self, model_path):
        self.menu_model = tf.keras.models.load_model(model_path)

    def _imageloader_from_path(self, image_path):
        # return np.array(Image.open(image_path).resize((480,360))).transpose(1,0,2)
        return np.array(Image.open(io.BytesIO(requests.get(image_path).content)).resize((480, 360))).transpose(1, 0, 2)

    def _imageloader_from_list(self, image_list):
        return np.array(image_list.resize((480, 360))).transpose(1, 0, 2)

    def _imageloader(self, image_list, image_path):
        if (image_list != None) and (image_path != None):
            return self._imageloader_from_list(image_list)
        elif (image_list == None) and (image_path != None):
            return self._imageloader_from_path(image_path)
        elif (image_list != None) and (image_path == None):
            return self._imageloader_from_list(image_list)
        else:
            print("Please input either image_list or image_path.")
            return None

    def pred_class(self, image_list=None, image_path=None):
        image = self._imageloader(image_list, image_path)
        return np.argmax(self.menu_model.predict(image.reshape(1, 480, 360, 3)))
