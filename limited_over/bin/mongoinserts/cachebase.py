import json
from django.contrib.staticfiles import finders


CACHE_LOCATION = "/temp/"


def get_item(key, default_value=None):
    try:
        base = str(finders.searched_locations[0])
    except IndexError:
        finders.find("")
        base = str(finders.searched_locations[0])
    location = base + CACHE_LOCATION + key + ".json"
    try:
        f = open(location)
        f.close()
    except FileNotFoundError:
        if default_value is not None:
            set_item(key, default_value)
        return default_value
    f = open(location, "r")
    x = json.load(f)
    f.close()
    return x


def set_item(key, value, indent=4):
    try:
        base = str(finders.searched_locations[0])
    except IndexError:
        finders.find("")
        base = str(finders.searched_locations[0])
    location = base + CACHE_LOCATION + key + ".json"
    f = open(location, "w+")
    f.write('{}')
    f.close()
    with open(location, "w+") as f:
        if indent == 0:
            json.dump(value, f, separators=(',', ':'))
        else:
            json.dump(value, f, indent=indent)
