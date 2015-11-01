# -*- coding: utf-8 -*-

__author__ = 'yw'

import os


def check_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def retry(attempt):
    def decorator(func):
        def wrapper(*args, **kw):
            att = 0
            while att < attempt:
                try:
                    return func(*args, **kw)
                except Exception as e:
                    att += 1

        return wrapper

    return decorator
