import json
import sys

def config_get(keys, cast=None):
    global cfg
    res = cfg
    for key in keys.split("."):
        res = res[key]

    if cast is not None:
        return cast(res)

    return res

def config_reload():
    global cfg
    cfg = {}
    for filename in sys.argv[1:]:
        if filename[-5:] == ".json":
            f = open(filename)
            data = json.load(f)
            config_update(cfg,data)

def config_update(cfg, data):
    for k,v in data.iteritems():
        if k not in cfg:
            cfg[k] = v
        elif isinstance(cfg[k], dict):
            config_update(cfg[k], data[k])
        else:
            cfg[k] = v
            
            
    

config_reload()
if __name__ == "__main__":
    print cfg
    config_get("capture.frequency", int)
