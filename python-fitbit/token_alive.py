#!/usr/bin/env python

from datetime import datetime
import json
import fitbit
import requests
import base64
import sys

#These are the secrets etc from Fitbit developer
OAuthTwoClientID = "22CMWS"
ClientOrConsumerSecret = "83418e86bc034c4f162277e411144aaa"
base64_key_secret = base64.b64encode(OAuthTwoClientID + ":" + ClientOrConsumerSecret)

#This is the Fitbit URL
TokenURL = "https://api.fitbit.com/oauth2/token"



now = str(datetime.now())
# file_name = "/Users/anthony/Desktop/python_api_puller/python-fitbit/pickletest.txt"
file_name = "/Users/anthony/Desktop/python_api_puller/python-fitbit/token.json"

token_pair = {"access_token" : "at1", "refresh_token" : "rf1", "time" : now}

def read():
    print("Reading...")
    file_obj = open(file_name, 'r')
    # s = file_obj.read()
    st = json.load(file_obj)
    a_token = st["access_token"]
    r_token = st["refresh_token"]
    print('\n' + a_token + " / " + r_token)
    file_obj.close()
    print("...Done reading")
    return {"access_token":a_token, "refresh_token":r_token}


def write():
    print("Writing...")
    
    file_obj = open(file_name, 'wb')
    # file_obj.write("access" + "\n")
    # file_obj.write("refresh" + "\n")
    # print(json.dumps(my))
    json.dump(token_pair, file_obj)
    file_obj.close()

    print("\tDone writing!")

def token_authorize():
    print("Authorizing...")
    
    AuthorisationCode = sys.argv[1]
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}

    BodyText = {'code' : AuthorisationCode,
            'redirect_uri' : 'https://jhprohealth.app/callback',
            'client_id' : OAuthTwoClientID,
            'grant_type' : 'authorization_code'}

    r = requests.post(TokenURL, headers=headers, data=BodyText)
    print(r.text)
    file_obj = open("token.json", 'wb')
    file_obj.write(r.text)
    file_obj.close()
    print("...Finished authorizing")
    return json.loads(r.text)


def token_refresh(token_dict):
    print("Refreshing...")
    
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}

    BodyText = {
            'refresh_token' : token_dict["refresh_token"],
            'grant_type' : 'refresh_token'}
    print(BodyText)

    r = requests.post(TokenURL, headers=headers, data=BodyText)
    print(r.text)
    file_obj = open("token.json", 'wb')
    file_obj.write(r.text)
    file_obj.close()
    print("...Finished refreshing")
    return json.loads(r.text)

def get_body_fat_log(token_dict):
    print("Getting body fat log")
    headers = {"Authorization":"Bearer " + token_dict["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/body/log/fat/date/2018-04-01/2018-04-29.json',
                      headers=headers)
    print(r.text)
    return r.text

def get_weight_log(token_dict):
    print("Getting weight log")
    headers = {"Authorization":"Bearer " + token_dict["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/body/log/weight/date/2018-05-07/2018-05-09.json',
                      headers=headers)
    print(r.text)
    return r.text

def get_activity_list(token_dict):
    print("Getting activity list")
    headers = {"Authorization":"Bearer " + token_dict["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/date/2018-04-13.json',
                      headers=headers)
    print(r.text)
    return r.text

def get_intraday_heart(token_dict):
    print("Getting Intraday HR")
    headers = {"Authorization":"Bearer " + token_dict["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/heart/date/2018-04-20/1d/1min.json',
                      headers=headers)
    print(r.text)
    return r.text

def get_intraday_activity(token_dict):
    print("Getting Intraday Activity in Steps")
    headers = {"Authorization":"Bearer " + token_dict["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/steps/date/2018-05-08/1d.json',
                      headers=headers)
    print(r.text)
    return r.text

def test(token_dict):
    print("RTOKEN" + token_dict["refresh_token"])

def main():
    if(len(sys.argv) == 2):
        print("Logging in with given AUTH CODE.")
        token_dict = token_authorize()
    elif(len(sys.argv) == 1):
        print("Logging in with previous token session.")
        token_dict = read()
    else:
        print("Needs one or no argument")
        sys.exit()
    token_dict = token_refresh(token_dict)
    get_body_fat_log(token_dict)
    get_weight_log(token_dict)
    get_activity_list(token_dict)
    get_intraday_heart(token_dict)
    get_intraday_activity(token_dict)

main()
