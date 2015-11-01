# -*- coding: utf-8 -*-

__author__ = 'yw'

import requests
import sys
from time import sleep
from util.util import retry

reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

HEADER_INFO = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/46.0.2490.80 Safari/537.36'
}


class OneCode(object):
    def __init__(self, _config):
        super(OneCode, self).__init__()
        self._config = _config
        self.token = 0
        self.url = 'http://www.yzm1.com/api/do.php'
        self.login()
        print self.token

    @retry(attempt=3)
    def login(self):
        payload = {
            'action': 'loginIn',
            'name': self._config['username'],
            'password': self._config['password']
        }
        status, token = requests.post(self.url, data=payload, headers=HEADER_INFO).content.split('|')
        if status:
            self.token = token

    @retry(attempt=3)
    def get_cell(self):
        payload = {
            'action': 'getPhone',
            'sid': 'id',
            'token': self.token,
        }
        phone = 0
        while 1:
            status, phone = requests.post(self.url, data=payload, headers=HEADER_INFO).content.split('|')
            if status == 0:
                sleep(3)
                continue
            else:
                break
        return phone

    def add_blacklist(self, phone):
        payload = {
            'action': 'addBlacklist',
            'sid': 'id',
            'token': self.token,
            'phone': phone
        }
        status, result = requests.post(self.url, data=payload, headers=HEADER_INFO).content.split('|')
        assert status == 1, 'Failed when release {}'.format(phone)

    @retry(attempt=3)
    def get_sms(self, phone):
        payload = {
            'action': 'getMessage',
            'sid': 'id',
            'phone': phone,
            'token': self.token
        }
        count = 0
        message = 0
        while 1:
            status, message = requests.post(self.url, data=payload, headers=HEADER_INFO).content.split('|')
            if status == 0:
                sleep(3)
                count += 1
            else:
                break
            if count > 60:
                self.add_blacklist(phone)
                break
        return message

    @retry(attempt=3)
    def get_balance(self):
        payload = {
            'action': 'getSummary',
            'token': self.token
        }
        resp = requests.post(self.url, data=payload, headers=HEADER_INFO)
        summary = resp.content.split('|')
        return summary[1]


if __name__ == '__main__':
    import json

    with open('account.json') as f:
        config = json.load(f)
    o = OneCode(config)
    print 'Balance:', o.get_balance()
