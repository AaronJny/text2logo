# -*- coding: utf-8 -*-
# @File  : text2logo.py
# @Author: AaronJny
# @Date  : 2019/08/29
# @Desc  : 根据给定的企业名称，自动生成logo
import base64
import json
import string
from io import BytesIO
import jieba
from PIL import Image, ImageDraw, ImageFont


class TextFormatter:
    """
    文本格式化器，用于去除文本中的无用信息
    """

    def __init__(self):
        # 配置字典
        self.config_data = self.read_config_data()
        # 英文字符集合
        self.letters = self.get_letters()

    @staticmethod
    def read_config_data():
        """
        读取配置信息，主要是城市、公司后缀之类的字典，
        用于辅助提取商号

        Returns:
            dict: 配置字典
        """
        with open('config_data.json', 'r', encoding='utf-8') as f:
            text = f.read()
        config_data = json.loads(text)
        return config_data

    @staticmethod
    def get_letters():
        """
        获取英文字符集合

        Returns:
            set: 英文字符集合
        """
        # 大小写字母
        letters = [letter for letter in string.ascii_letters]
        # 数字0-9字符
        letters.extend(list(map(str, range(10))))
        letters.extend([' ', '.'])
        # 使用set提高查询效率
        letters = set(letters)
        return letters

    def extract_trade_name(self, text):
        """
        对文本数据进行处理，提取商号

        Args:
            text: 待提取商号的文本

        Returns:
            str: 提取出的商号
        """
        # 将全角括号转换为半角括号
        text = text.replace('（', '(').replace('）', ')')
        # 移除文本中的括号及括号内的内容
        while '(' in text and ')' in text:
            lindex = text.index('(')
            rindex = text.index(')')
            if lindex > rindex:
                break
            text = text[:lindex] + text[rindex + 1:]
        # 使用特定字符切分字符串，如`/`,`-`等
        split_chars = self.config_data['split_chars']
        for ch in split_chars:
            # 注意，这里是循环切割，最后text相当于在原text使用这些字符切割后，
            # 最前面的一个元素
            text = text.split(ch)[0]
        # 移除城市特征
        cities = self.config_data['cities']
        for city in cities:
            text = text.replace(city, '')
        # 移除公司后缀
        company_suffixes = self.config_data['company_suffixes']
        for suffix in company_suffixes:
            text = text.replace(suffix, '')
        # 返回商号
        return text

    def cal_text_length(self, text):
        """
        计算文本显示需要的单位长度数量。
        英文字符为0.5单位长度，中文单位为1单位长度

        Args:
            text: 需要计算长度的本文

        Returns:
            float: 给定文本显示需要的单位长度数量
        """
        length = 0
        for ch in text:
            if ch in self.letters:
                length += 0.5
            else:
                length += 1
        return length

    def array_text(self, text):
        """
        对给定文本进行分词，并根据分词结果和单词长度，安排文字在图片上显示的位置（通过加入换行和空白来实现）。
        同时，计算文字在图片上占据的高和宽

        Args:
            text[str]: 需要显示的文本

        Returns:
            str,int,int: 处理后的文本，文本最大宽度，文本高度
        """
        # 先对文本进行分词
        words = list(jieba.cut(text))
        # 用于按行保存要在图片上显示的文本的列表
        _res = []
        # 当前行缓存字符串
        current_buff = ''
        # 遍历分词结果，图片上每行最多显示6个单位长度，如果当前行长度超过6单位长度，
        # 则另起一行，将单词加入到新行中
        for word in words:
            if self.cal_text_length(current_buff + word) <= 6:
                current_buff = current_buff + word
            else:
                _res.append(current_buff)
                current_buff = word
        if current_buff:
            _res.append(current_buff)
        # 计算所有行中，最长的那一行的长度
        max_width = max(map(self.cal_text_length, _res))
        # 计算总行数
        max_height = len(_res)
        # 对上面的数据重新加工一下，通过添加空白的方式，使得文本居中显示
        res = []
        for seq in _res:
            # 计算需要填充的空白数
            padding_spaces = max_width - self.cal_text_length(seq)
            # 进行填充
            res.append('  ' * int(padding_spaces) + seq + ' ' * int(padding_spaces))
        # 将所有行的文本使用换行符拼接成一个文本，返回(拼接后文本，最大宽度，最大高度)
        return '\n'.join(res), max_width, max_height


class Converter:
    """
    能够将企业名称转换成logo的转换器
    """

    def __init__(self, colors=None, font_path='NotoSansCJKsc-Regular.otf'):
        # 文字配色
        if colors:
            self.bg_color, self.front_color = colors
        else:
            self.bg_color, self.front_color = '34495e', 'ecf0f1'
        # 显示字体
        self.font_path = font_path
        # 用于处理文本的格式化器
        self.text_formatter = TextFormatter()

    @staticmethod
    def hex2rgb(hex_color):
        """
        将16进制颜色编码，转换为rgb格式

        Args:
            hex_color[str]: 16进制颜色编码

        Returns:
            tuple: (r,g,b)
        """
        if isinstance(hex_color, str):
            color = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)
        elif (isinstance(hex_color, tuple) or isinstance(hex_color, list)) and len(hex_color) == 3:
            color = hex_color
        else:
            raise Exception('给定的图片配色不正确！')
        return color

    def text2image(self, text, font_size=48, width=400, height=140, need_extracted=True, need_arrayed=True,
                   show_image=False):
        """
        将给定文字转换成指定大小的图片。
        可以通过调整参数改变图片的效果。

        Args:
            text: 需要转换成图片的文本
            font_size: 文字大小
            width: 图片的宽度，默认 400
            height: 图片的高度，默认 140
            need_extracted: 如果给定的文本是公司名称，是否需要提取商号来生成图片，默认进行提取
            need_arrayed: 是否需要通过分词等处理方法，对文本进行排列，获得更好的显示效果，默认进行处理
            show_image: 是否显示图片，默认不显示

        Returns:
            str: 生成的图片的base64转码
        """
        # 如果需要，从文本中提取商号，替代原文本
        if need_extracted:
            text = self.text_formatter.extract_trade_name(text)
        # 如果需要，对文本进行排列，以获得更好的显示效果
        if need_arrayed:
            text, max_width, max_height = self.text_formatter.array_text(text)
        else:
            max_width = self.text_formatter.cal_text_length(text)
            max_height = 1
        # 获取rgb配色
        bg_color = self.hex2rgb(self.bg_color)
        front_color = self.hex2rgb(self.front_color)
        # 开始绘制
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, font_size)
        # 按字体大小缩放，计算真实宽高
        w = max_width * font_size
        h = max_height * font_size
        # 居中
        draw.text(((width - w) / 2, (height - h) / 2), text, font=font, fill=front_color)
        del draw
        # 转RGB
        img = img.convert('RGB')
        # 如果需要，就显示图片
        if show_image:
            img.show()
        # 将图片转为base64字符串返回
        output_buffer = BytesIO()
        img.save(output_buffer, format='JPEG')
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data).decode('utf8')
        return base64_str
