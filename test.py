# -*- coding: utf-8 -*-
# @File  : test.py
# @Author: AaronJny
# @Date  : 2019/08/29
# @Desc  :
from text2logo import Converter


def run():
    converter = Converter()
    img_base64_str = converter.text2image('轻松筹/众筹空间', font_size=100, show_image=True)
    print(img_base64_str)


if __name__ == '__main__':
    run()
