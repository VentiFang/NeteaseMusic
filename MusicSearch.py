# -*- coding:utf-8 -*-
import requests, hashlib, sys, click, re, base64, binascii, json, os
from Cryptodome.Cipher import AES
from http import cookiejar

"""
Website:http://cuijiahua.com
Author:Jack Cui
Refer:https://github.com/darknessomi/musicbox
"""


class Encrypyed():
    """
    解密算法
    """

    def __init__(self):
        self.modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        self.nonce = '0CoJUm6Qyw8W8jud'
        self.pub_key = '010001'

    # 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox脚本实现
    def encrypted_request(self, text):
        text = json.dumps(text)
        sec_key = self.create_secret_key(16)
        enc_text = self.aes_encrypt(self.aes_encrypt(text, self.nonce), sec_key.decode('utf-8'))
        enc_sec_key = self.rsa_encrpt(sec_key, self.pub_key, self.modulus)
        data = {'params': enc_text, 'encSecKey': enc_sec_key}
        return data

    def aes_encrypt(self, text, secKey):
        pad = 16 - len(text) % 16
        text = text + chr(pad) * pad
        encryptor = AES.new(secKey.encode('utf-8'), AES.MODE_CBC, b'0102030405060708')
        ciphertext = encryptor.encrypt(text.encode('utf-8'))
        ciphertext = base64.b64encode(ciphertext).decode('utf-8')
        return ciphertext

    def rsa_encrpt(self, text, pubKey, modulus):
        text = text[::-1]
        rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
        return format(rs, 'x').zfill(256)

    def create_secret_key(self, size):
        return binascii.hexlify(os.urandom(size))[:16]


class Song():
    """
    歌曲对象，用于存储歌曲的信息
    """

    def __init__(self, song_id, song_name, song_num, song_url=None):
        self.song_id = song_id
        self.song_name = song_name
        self.song_num = song_num
        self.song_url = '' if song_url is None else song_url


class Crawler():
    """
    网易云爬取API
    """

    def __init__(self, timeout=60, cookie_path='.'):
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.cookies = cookiejar.LWPCookieJar(cookie_path)
        self.download_session = requests.Session()
        self.timeout = timeout
        self.ep = Encrypyed()

    def post_request(self, url, params):
        """
        Post请求
        :return: 字典
        """

        data = self.ep.encrypted_request(params)
        resp = self.session.post(url, data=data, timeout=self.timeout)
        result = resp.json()
        if result['code'] != 200:
            click.echo('post_request error')
        else:
            return result

    def search(self, search_content, search_type, limit=9):
        """
        搜索API
        :params search_content: 搜索内容
        :params search_type: 搜索类型
        :params limit: 返回结果数量
        :return: 字典.
        """
        url = 'http://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        params = {'s': search_content, 'type': search_type, 'offset': 0, 'sub': 'false', 'limit': limit}
        result = self.post_request(url, params)
        return result

    def search_song(self, song_name, limit=99):
        result = self.search(song_name, search_type=1, limit=limit)
        if result['result']['songCount'] <= 0:
            click.echo('Song {} not existed.'.format(song_name))
        else:
            songs = result['result']['songs']
            return songs


    def get_song_by_id(self, song_id):
        from downloadMusic import main
        main(song_id)


class Netease():
    """
    网易云音乐下载
    """

    def __init__(self, timeout, folder, quiet, cookie_path):
        self.crawler = Crawler(timeout, cookie_path)
        self.folder = '.' if folder is None else folder
        self.quiet = quiet

    def download_song_by_search(self, song_name):
        songs = self.crawler.search_song(song_name)
        song = self.select_one_song(songs)
        self.download_song_by_id(song.song_id)

    def download_song_by_id(self, song_id):
        self.crawler.get_song_by_id(song_id)

    def select_one_song(self, songs):
        for index, musicINFO in enumerate(songs):
            print("序号: %s" % index, '  歌曲名:', musicINFO['name'], '   网易云曲歌ID:', musicINFO['id'], '    艺术家:',
                  [ar['name'] for ar in musicINFO['ar']])

        index = int(input("请输入要下载歌曲的序号: "))
        song_id, song_name = songs[index]['id'], songs[index]['name']
        song = Song(song_id=song_id, song_name=song_name, song_num=index)
        return song


if __name__ == '__main__':
    timeout = 60
    output = 'Musics'
    quiet = False
    cookie_path = 'Cookie'
    netease = Netease(timeout, output, quiet, cookie_path)
    print("--------------网易云音乐在线下载--------------")
    song_name = input("请输入想要下载的歌曲名称: ")
    netease.download_song_by_search(song_name)
