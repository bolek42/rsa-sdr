import json
import sys
import os
import getopt

cfg = {}
config_file = ""
args = []

_doc_="""python2 %s [args]
Misc:
    -h / --help                     This help
    --config=config/test.json       File to save config. if it does not exist, it will be created with default parameter
    --dut=dut.py                    Device under test class

Capture:
    --capture-frequency=125.5e6      Frequency to capture
    --capture-samp-rate=2e6          Capture sample rate
    --capture-gain=41                Capture gain
""" % sys.argv[0]
def usage():
    print _doc_
    sys.exit(1)


def config_get(keys, cast=None):
    global cfg
    res = cfg
    for key in keys.split("."):
        res = res[key]

    if cast is not None:
        return cast(res)

    return res

def config_set(key, value, cast=None):
    global cfg

    if cast is not None:
        value = cast(value)

    c = cfg
    for k in key.split(".")[:-1]:
        c = c[k]

    c[key.split(".")[-1]] = value

    with open(config_file, "w") as f:
        f.write(json.dumps(cfg, indent=4))

def config_reload():
    global cfg
    global config_file
    global args

    if len(sys.argv[1:]) == 0:
        usage()

    opt_short = "h"
    opt_long = ["help", "config=", "dut=", "capture-frequency=", "capture-gain=", "capture-samp-rate="]
    (opts,args) = getopt.getopt(sys.argv[1:], opt_short, opt_long)

    cfg = {}
    for o,v in opts:
        if o in ("-h", "--help"):
            usage()

        elif o == "--config":
            config_file = v

            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    cfg = json.load(f)
            else:
                with open("config/default.json", "r") as f:
                    cfg = json.load(f)

        elif o == "--dut":
            config_set("dut", v, str)

        elif o == "--capture-frequency":
            config_set("capture.frequency", v, float)

        elif o == "--capture-gain":
            config_set("capture.gain", v, int)

        elif o == "--capture-samp-rate":
            config_set("capture.samp_rate", v, float)

        else:
            usage()



config_reload()
if __name__ == "__main__":
    print json.dumps(cfg, indent=4)
    config_get("capture.frequency", int)
