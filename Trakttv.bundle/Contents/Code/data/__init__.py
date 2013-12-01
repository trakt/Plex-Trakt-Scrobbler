import sys

# Will inject modules into sys.modules manually for money...

import dict_object
sys.modules['data.dict_object'] = dict_object

import client
sys.modules['data.client'] = client

import user
sys.modules['data.user'] = user

import watch_session
sys.modules['data.watch_session'] = watch_session
