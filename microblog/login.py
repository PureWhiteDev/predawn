# -*- coding: utf-8 -*-

__author__ = 'yw'

import pickle
import os
import requests
import sys

from pyquery import PyQuery

reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

HEADER_INFO = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/46.0.2490.71 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4'
}


def check_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


class MicroBlog(object):
    def __init__(self, account):
        super(MicroBlog, self).__init__()
        self.sess = requests.Session()
        self.account = account
        check_dir('cookies')

    def login(self):
        login_url = 'http://login.weibo.cn/login/'
        resp = self.sess.get(login_url, headers=HEADER_INFO)
        doc = PyQuery(resp.content)
        form = doc('form')
        url_suffix = form.attr.action
        vk_value = None
        pwd_name = None
        for i in form.find('input').items():
            if i.attr.name == 'vk':
                vk_value = i.attr.value
            if i.attr.type == 'password':
                pwd_name = i.attr.name
        assert vk_value is not None and pwd_name is not None
        payload = {
            'mobile': self.account['username'],
            pwd_name: self.account['password'],
            'remember': 'on',
            'backURL': 'http%3A%2F%2Fweibo.cn',
            'backTitle': u'手机新浪网',
            'submit': u'登录',
            'vk': vk_value
        }
        index_page = self.sess.post(url=login_url + url_suffix, data=payload, headers=HEADER_INFO)
        captcha_page = PyQuery(index_page.content)
        if captcha_page('.me') and u'验证码' in captcha_page('.me').text():
            self.login_again(captcha_page)

    def login_again(self, captcha_page):
        form = captcha_page('form')
        url_suffix = form.attr.href
        captcha_img_url = form('img:first').attr.src
        with open('captcha.gif', 'wb') as f:
            f.write(self.sess.get(captcha_img_url, headers=HEADER_INFO).content)

        # to do:
        # need to recognize automatically here

        captcha_recognized = raw_input('NOW input captcha plz:')
        vk_value = None
        pwd_name = None
        captcha_id = None
        for i in form.find('input').items():
            if i.attr.name == 'vk':
                vk_value = i.attr.value
            if i.attr.type == 'password':
                pwd_name = i.attr.name
            if i.attr.name == 'capId':
                captcha_id = i.attr.value
        assert vk_value is not None and pwd_name is not None and captcha_id is not None
        payload = {
            'mobile': self.account['username'],
            pwd_name: self.account['password'],
            'remember': 'on',
            'backURL': 'http%3A%2F%2Fweibo.cn',
            'backTitle': u'手机新浪网',
            'submit': u'登录',
            'vk': vk_value,
            'code': captcha_recognized,
            'capId': captcha_id
        }
        result = self.sess.post('http://login.weibo.cn/login/{}'.format(url_suffix), data=payload)
        with open('result.html', 'w') as f:
            f.write(result.content)

    def init_session(self):
        try:
            with open('cookies/{}'.format(self.account['username']), 'rb') as f:
                self.sess.cookies = pickle.load(f)
                # self.sess.get('http://weibo.cn/', cookies=cookies)
        except IOError:
            self.login()
            with open('cookies/{}'.format(self.account['username']), 'wb') as f:
                pickle.dump(self.sess.cookies, f)

    def follow(self, target_user):
        self.init_session()
        with open('tst.html', 'w') as f:
            f.write(self.sess.get('http://weibo.cn/find/?tf=5_007&vt=4', headers=HEADER_INFO).content)
        url = 'http://weibo.cn/find/user?vt=4'
        payload = {
            'keyword': target_user,
            'suser': 2
        }
        # test
        if target_user == '28yangw':
            return
        search_result = self.sess.post(url, data=payload, headers=HEADER_INFO)
        doc = PyQuery(search_result.content).make_links_absolute(search_result.url)
        target = {
            'is_locked': 0,
            'is_followed': 1,
            'follow_link': None,
            'homepage': None
        }
        for i in doc('body > table').eq(0)('a').items():
            if i.text() == target_user:
                target['is_locked'] = 1
                target['homepage'] = i.attr.href
            if i.text() == u'关注他' or u'关注她':
                target['is_followed'] = 0
                target['follow_link'] = i.attr.href
        if target['is_locked'] and not target['is_followed']:
            print 'target locked: {}'.format(target_user)
            resp = self.sess.get(target['follow_link'], headers=HEADER_INFO)
            with open('follow_result_page.html', 'w') as f:
                f.write(resp.content)

    def visit_test(self, url):
        with open('logged_index_page.html', 'w') as f:
            f.write(self.sess.get(url, headers=HEADER_INFO).content)


if __name__ == '__main__':
    name = raw_input('username:')
    pwd = raw_input('password:')
    t_account = dict(username=name, password=pwd)
    m = MicroBlog(t_account)
    m.init_session()
    m.visit_test('http://weibo.cn/?vt=4')
