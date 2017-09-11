# Copyright (c) 2017 Pavel 'Blane' Tuchin


def handler(name, srv):
    def augment(h):
        h.name = name
        h.service = srv
        return h
    return augment
