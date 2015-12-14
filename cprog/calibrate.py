import time

while 1:
    print "Busy"
    for i in xrange(40000000): pass
    print "Idle"
    time.sleep(1)
