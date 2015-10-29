# -*- coding: utf-8 -*-

__author__ = 'yw'

import os

def check_dir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
