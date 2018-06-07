#!/usr/bin/env python

from datetime import datetime
import json

now = str(datetime.now())
file_name = "/Users/anthony/Desktop/python_api_puller/python-fitbit/pickletest.txt"
token_pair = {"access_token" : "atatatat", "refresh_token" : "rfrfrfrfrf", "time" : now}

def write():
    print("Writing...")
    
    file_obj = open(file_name, 'wb')
    # file_obj.write("access" + "\n")
    # file_obj.write("refresh" + "\n")
    # print(json.dumps(my))
    json.dump(token_pair, file_obj)
    file_obj.close()

    print("\tDone writing!")

def read():
    print("Reading...")
    file_obj = open(file_name, 'r')
    s = file_obj.read()
    print("\tDone reading...")
    print("\t" + s)
    file_obj.close()

write()
read()