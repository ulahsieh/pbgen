#/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import OrderedDict

################################################################################
def ordered_dict(*keys, **kwargs):
    params = OrderedDict()
    for key in keys:
        if key in kwargs:
            params[key] = kwargs[key]
    return params

################################################################################
def apt(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['apt'] = ordered_dict(
        'name', 'state', 'update_cache', 'force_apt_get', 
        kwargs
    )
    return module

################################################################################
def apt_key(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['apt_key'] = ordered_dict(
        'url', 'state', 
        kwargs
    )
    return module

################################################################################
def apt_repository(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['apt_repository'] = ordered_dict(
        'repo', 'state', 
        kwargs
    )
    return module

################################################################################
def docker_image(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['docker_image'] = ordered_dict(
        'name', 'source', 
        kwargs
    )
    return module

################################################################################
def file(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['file'] = ordered_dict(
        'src', 'dest', 'state', 
        kwargs
    )
    return module

################################################################################
def filesystem(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['filesystem'] = ordered_dict(
        'device', 'force', 'fstype', 
        kwargs
    )
    return module

################################################################################
def get_url(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['get_url'] = ordered_dict(
        'url', 'dest', 'mode', 
        kwargs
    )
    return module

################################################################################
def mount(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['mount'] = ordered_dict(
        'path', 'src', 'fstype', 'state', 
        kwargs
    )
    return module

################################################################################
def parted(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['parted'] = ordered_dict(
        'device', 'number', 'state', 
        kwargs
    )
    return module

################################################################################
def pip(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['pip'] = ordered_dict(
        'name', 'state', 
        kwargs
    )
    return module

################################################################################
def shell(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['shell'] = ordered_dict(
        'shell', 
        kwargs
    )
    return module

################################################################################
def user(**kwargs):
    module = OrderedDict()
    if 'desc' in kwargs: module['name'] = kwargs['desc']
    module['shell'] = ordered_dict(
        'name', 'groups', 'append', 
        kwargs
    )
    return module
