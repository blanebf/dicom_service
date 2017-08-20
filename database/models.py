# Copyright (c) 2017 Pavel 'Blane' Tuchin
from peewee import *

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


def init_sqlite(filename):
    db = SqliteDatabase(filename)
    database_proxy.initialize(db)
