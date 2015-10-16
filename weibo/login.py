# -*- coding: utf-8 -*-

__author__ = 'yw'

import json
import os
import requests
import sys

from pyquery import PyQuery

reload(sys)
sys.setdefaultencoding('utf-8')

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

class WeiboSession(object):
    def __init__(self, account):
        super(WeiboSession, self).__init__()
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
        return index_page

    def get_session(self):
        try:
            with open('cookies/{}'.format(self.account['username'])) as f:
                cookies = json.load(f)
            self.sess.get('http://weibo.cn/', cookies=cookies)
        except IOError:
            self.login()
            with open('cookies/{}'.format(self.account['username']), 'w') as f:
                json.dump(self.sess.cookies.get_dict(), f, encoding='utf-8')

    def follow(self):
        target_user = None
        self.get_session()
        url = 'http://weibo.cn/find/user?vt=4'
        payload = {
            'keyword': target_user,
            'suser': 2
        }
        # test
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


if __name__ == '__main__':
    test = {
        'username': '',
        'password': ''
    }
    w = WeiboSession(test)
    w.follow()
