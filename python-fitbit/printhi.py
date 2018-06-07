#!/usr/bin/env python

from datetime import datetime

now = str(datetime.now())

# Open a file
fo = open("/Users/anthony/Desktop/python_api_puller/python-fitbit/foo.txt", "a")
fo.write("Cron testing: " + now + '\n');

# Close opend file
fo.close()