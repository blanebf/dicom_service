# Copyright (c) 2017 Pavel 'Blane' Tuchin
from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

database_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = database_proxy


def init_sqlite(filename):
    db = SqliteExtDatabase(filename)
    database_proxy.initialize(db)
