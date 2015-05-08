from mongokit import Connection
import re


connection = Connection()


def remove_unuse_character(originstr):
    return re.sub(r'\r\n|\s+', '', originstr)
