# -*- coding: utf-8 -*-

__author__ = 'yw'

import pickle
import os
import requests
import sys

from pyquery import PyQuery
from urlparse import urlparse, parse_qs

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
        self.parm_st = account.get('st', None)
        self.gid = account.get('gid', None)
        self.uid = account.get('uid', None)
        check_dir('cookies')
        check_dir('param_st')
        self.init_session()

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
        captcha_page = PyQuery(index_page.content).make_links_absolute(index_page.url)
        temp_link = None
        for retry in xrange(5):
            if captcha_page('.me') and u'验证码' in captcha_page('.me').text():
                result = self.login_again(captcha_page)
                captcha_page = PyQuery(result.content).make_links_absolute(result.url)
            if captcha_page('.tip2 > a:last').text().startswith('@'):
                for a_link in captcha_page('.c').eq(1)('div').eq(1)('a').items():
                    if a_link.text().startswith(u'赞'):
                        temp_link = a_link.attr.href
                break
        if temp_link:
            # http://weibo.cn/attitude/D0XKRAF2R/add?uid=3805388718&rl=0&gid=10001&vt=4&st=8f29d3
            parser = urlparse(temp_link)
            temp_dict = parse_qs(parser.query)
            self.gid = temp_dict['gid'][0]
            self.uid = temp_dict['uid'][0]
            self.parm_st = temp_dict['st'][0]

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
        return result

    def init_session(self):
        try:
            with open('cookies/{}'.format(self.account['username']), 'rb') as f:
                self.sess.cookies = pickle.load(f)
                # self.sess.get('http://weibo.cn/', cookies=cookies)
        except IOError:
            self.login()
            with open('cookies/{}'.format(self.account['username']), 'wb') as f:
                pickle.dump(self.sess.cookies, f)

    def follow(self, target_user, prefix=None):
        if prefix is not None and self.parm_st is not None:
            url = '{0}&st={1}'.format(prefix, self.parm_st)
            print 'target url: {}'.format(url)
            self.sess.get(url, headers=HEADER_INFO)
        else:
            url = 'http://weibo.cn/find/user?vt=4'
            payload = {
                'keyword': target_user,
                'suser': 2
            }
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
                prefix, suffix = target['follow_link'].rsplit('&st=')
                with open('param_st/{}'.format(self.account['username']), 'w') as f:
                    f.write(suffix)
        return prefix

    def locate_post(self, post_owner, post_digest):
        url = 'http://weibo.cn/find/user?vt=4'
        payload = {
            'keyword': post_owner,
            'suser': 2
        }
        search_result = self.sess.post(url, data=payload, headers=HEADER_INFO)
        doc = PyQuery(search_result.content).make_links_absolute(search_result.url)
        owner_homepage = None
        for i in doc('body > table').eq(0)('a').items():
            if i.text() == post_owner:
                owner_homepage = i.attr.href
                break
        post_relative = {}
        post_pq = None
        if owner_homepage:
            home_resp = self.sess.get(owner_homepage, headers=HEADER_INFO)
            doc = PyQuery(home_resp).make_links_absolute(home_resp.url)
            for i in doc('.c').items():
                if i.attr.id:
                    if i('div:last').text().strip().startswith(post_digest):
                        post_pq = i('div:last')
        '''
        # like http://weibo.cn/attitude/D0XIq1BSe/add?uid=3805388718&rl=0&vt=4&st=8f29d3
        # repost http://weibo.cn/repost/D0XIq1BSe?uid=1687024994&rl=0&vt=4
        # comment http://weibo.cn/comment/D0XIq1BSe?uid=1687024994&rl=0&vt=4#cmtfrm
        # fav http://weibo.cn/fav/addFav/D0XIq1BSe?rl=0&vt=4&st=8f29d3
        '''
        if post_pq:
            parser = urlparse(post_pq('.cc').attr.href)
            post_id = parser.path.rsplit('/')[-1]
            poster_uid = parse_qs(parser.query)['uid'][0]
            post_relative = {
                'id': post_id,
                'srcuid': poster_uid
            }
        return post_relative

    def repost(self, post_relative, content):
        url = 'http://weibo.cn/repost/dort/{}'.format(post_relative['id'])
        params = {
            'vt': 4,
            'st': self.parm_st
        }
        payload = {
            'act': 'dort',
            'rl': 1,
            'id': post_relative['id'],
            'content': content,
            'rtkeepreason': 'on'
        }
        self.sess.post(url, params=params, data=payload, headers=HEADER_INFO)

    def comment(self, post_relative, content):
        url = 'http://weibo.cn/comments/addcomment'
        params = {
            'vt': 4,
            'st': self.parm_st
        }
        payload = {
            'srcuid': post_relative['srcuid'],
            'id': post_relative['id'],
            'rl': 1,
            'content': content
        }
        self.sess.post(url, data=payload, params=params, headers=HEADER_INFO)

    def comment_with_repost(self, post_relative, content):
        url = 'http://weibo.cn/comments/addcomment'
        params = {
            'vt': 4,
            'st': self.parm_st
        }
        payload = {
            'srcuid': post_relative['srcuid'],
            'id': post_relative['id'],
            'rl': 1,
            'content': content,
            'rt': u'评论并转发'
        }
        self.sess.post(url, data=payload, params=params, headers=HEADER_INFO)

    def like(self, post_relative):
        url = 'http://weibo.cn/attitude/{}/add'.format(post_relative['id'])
        payload = {
            'uid': self.uid,
            'rl': 0,
            'vt': 4,
            'st': self.parm_st
        }
        self.sess.get(url, params=payload, headers=HEADER_INFO)

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
    follow_target = raw_input('target person name:')
    follow_url = m.follow(follow_target)
    common_url = follow_url.rsplit('&st=')
