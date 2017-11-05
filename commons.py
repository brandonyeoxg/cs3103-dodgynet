#!/usr/bin/env python3

import hashlib
import logging

logger_debug_format = '%(asctime)s %(levelname)-8s'\
' [%(process)-5d] %(filename)s +%(lineno)s: %(message)s'
logger_consumer_format = '%(message)s'

ascii_art_logo = """\

 /$$$$$$$                  /$$                     /$$   /$$             /$$    
| $$__  $$                | $$                    | $$$ | $$            | $$    
| $$  \ $$  /$$$$$$   /$$$$$$$  /$$$$$$  /$$   /$$| $$$$| $$  /$$$$$$  /$$$$$$  
| $$  | $$ /$$__  $$ /$$__  $$ /$$__  $$| $$  | $$| $$ $$ $$ /$$__  $$|_  $$_/  
| $$  | $$| $$  \ $$| $$  | $$| $$  \ $$| $$  | $$| $$  $$$$| $$$$$$$$  | $$    
| $$  | $$| $$  | $$| $$  | $$| $$  | $$| $$  | $$| $$\  $$$| $$_____/  | $$ /$$
| $$$$$$$/|  $$$$$$/|  $$$$$$$|  $$$$$$$|  $$$$$$$| $$ \  $$|  $$$$$$$  |  $$$$/
|_______/  \______/  \_______/ \____  $$ \____  $$|__/  \__/ \_______/   \___/  
                               /$$  \ $$ /$$  | $$                              
                              |  $$$$$$/|  $$$$$$/                              
                               \______/  \______/                               
"""

def md5sum(fd):
    md5 = hashlib.md5()
    length = md5.block_size * 128
    return md5sum_bytes(fd.read(length))

def md5sum_bytes(bytes):
    md5 = hashlib.md5()
    for chunk in iter(lambda: bytes, b''):
        md5.update(chunk)
    digest = md5.digest()
    logging.debug("Digest: %s" % md5.hexdigest())
    return digest


# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
