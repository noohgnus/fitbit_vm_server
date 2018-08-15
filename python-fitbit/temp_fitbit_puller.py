#!/usr/bin/env python
import json
import datetime
import MySQLdb as db

import json
import fitbit
import requests
import base64
import sys

class FitbitTimeSet:
    def __init__(self, heart_rate=0, step_count=0, activity_level=0, distance=0, uid="***NO UID SUPPLIED***"):
        self.heart_rate = heart_rate
        self.step_count = step_count
        self.activity_level = activity_level
        self.distance = distance
        self.uid = uid

    def __repr__(self):
        return "FitbitTimeSet(" + str(self.heart_rate) + ',' + str(self.step_count) + ',' + str(self.activity_level) + ',' + self.uid + ")"

#These are the secrets etc from Fitbit developer
OAuthTwoClientID = "22CMWS"
ClientOrConsumerSecret = "83418e86bc034c4f162277e411144aaa"
base64_key_secret = base64.b64encode(OAuthTwoClientID + ":" + ClientOrConsumerSecret)

#This is the Fitbit URL
TokenURL = "https://api.fitbit.com/oauth2/token"

#Remote database info
HOST = "10.162.80.9"
PORT = 3306
USER = "fitbitter"
PASSWORD = "yiGLeVihDHhQMJPo"
DB = "mmcfitbit"

now = str(datetime.datetime.now())
file_name = "/Users/anthony/Desktop/python_api_puller/python-fitbit/token.json"

def get_multi_token_dict():
    print("Reading in from existing tokens.json ...")
    file_obj = open("tokens.json", 'r')
    st = json.load(file_obj)
    file_obj.close()
    print("\t...Done reading tokens.json.")
    return st

def multi_login_routine():
    if(len(sys.argv) == 3):
        token_dict = get_multi_token_dict()
        refresh_user_token(token_dict, sys.argv[1], sys.argv[2])
    elif(len(sys.argv) == 4):
        token_dict = get_multi_token_dict()
        refresh_user_token(token_dict, sys.argv[1], sys.argv[2])
    elif(len(sys.argv) == 2 and sys.argv[1] == "flush"):
        flush_temp_db()
        print("Temp DB flushed.")
        sys.exit()
    else:
        print("invalid arguments")
        sys.exit()
    # token_dict = token_refresh(token_dict)
    return token_dict

def refresh_user_token(token_dict, uid, start_time):
    json_user_datas = token_dict
    # print(json_user_datas)
    if uid not in json_user_datas["users"]:
        print("User id " + uid + " does not exist. Check the DB for your matching user_id.")
        exit()
    
    print("Pulling user : " + str(json_user_datas["users"][uid]["user_id"]))
    headers = {'Authorization':'Basic ' + base64_key_secret,
               'Content-Type':'application/x-www-form-urlencoded'}
    print("Using refresh_token -> " + str(json_user_datas["users"][uid]["refresh_token"]))
    BodyText = {
            'refresh_token' : json_user_datas["users"][uid]["refresh_token"],
            'grant_type' : 'refresh_token'}
    r = requests.post(TokenURL, headers=headers, data=BodyText)


    if(r.status_code != 200):
        print(r.text)
        raise Exception("While refreshing user " + uid + " , HTTP returned code ", str(r.status_code))
    else:
        # print(r.text)
        response = json.loads(r.text)
        json_user_datas["users"][uid]["access_token"] = response["access_token"]
        json_user_datas["users"][uid]["refresh_token"] = response["refresh_token"]
        json_user_datas["users"][uid]["modified_at"] = str(datetime.datetime.now())
        data_retrieval_routine(json_user_datas, uid, start_time)

    write_file = open("tokens.json", 'w+')
    json.dump(json_user_datas, write_file, indent=4)
    write_file.close()

    print("\t...Done refreshing")
    return json_user_datas

def data_retrieval_routine(token_dict, uid, start_time):
    date_string = start_time
    # date_string = "2018-06-01"
    try:
        execute_heart_and_step(token_dict, uid, date_string)
    except ValueError as ve:
        print ve

    print "\t-------data as of: " + start_time + "-------"

def execute_heart_and_step(token_dict, uid, date_string):
    heart_json = get_intraday_heart(token_dict, uid, date_string)
    step_json = get_intraday_activity(token_dict, uid, date_string)
    distance_json = get_intraday_distance(token_dict, uid, date_string)
        
    sedentary_payload =  get_activity_details(token_dict, uid, date_string, "minutesSedentary")
    light_active_payload = get_activity_details(token_dict, uid, date_string, "minutesLightlyActive")
    fairly_active_payload = get_activity_details(token_dict, uid, date_string, "minutesFairlyActive")
    very_active_payload = get_activity_details(token_dict, uid, date_string, "minutesVeryActive")
    activity_dict = combine_activity_levels(sedentary_payload, light_active_payload, fairly_active_payload, very_active_payload)
    
    time_dict = make_intraday_dict_from_json_datas(heart_json, step_json, distance_json, activity_dict, uid)
    insert_intraday_dict(time_dict)


############################################################
#                                                          #
# Fitbit API calling functions                             #
#                                                          #
############################################################


def get_activity_details(token_dict, uid, query_date, activity_resource_path):
    print("Getting activity details")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get('https://api.fitbit.com/1/user/-/activities/%s/date/%s/1d.json' % (activity_resource_path, query_date),
                      headers=headers)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    
    return r.text

def get_intraday_heart(token_dict, uid, query_date):
    print("Getting Intraday HR")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/activities/heart/date/" + query_date + "/1d/1min.json",
                      headers=headers)
    # print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting intraday heartrate")

    return r.text

def get_intraday_activity(token_dict, uid, query_date):
    print("Getting Intraday Activity in Steps")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/activities/steps/date/" + query_date + "/1d.json",
                      headers=headers)
    print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting intraday steps")

    return r.text

def get_intraday_distance(token_dict, uid, query_date):
    print("Getting Intraday Activity in Steps")
    headers = {"Authorization":"Bearer " + token_dict["users"][uid]["access_token"]}
    r = requests.get("https://api.fitbit.com/1/user/-/activities/distance/date/" + query_date + "/1d.json",
                      headers=headers)
    # print(r.text)
    if(r.status_code != 200):
        print(">\n>>\n>>>ERROR: GETTING HTTP " + str(r.status_code) + " with UID " + uid)
        print(r.text)
        raise AssertionError("API call response is other than 200 OK.")
    print("\t...Done getting intraday distance")

    return r.text

def make_intraday_dict_from_json_datas(heart_rate_json, step_count_json, distance_json, activity_level_dict, uid):
    print("Converting HR and Step JSON data to dictionary...")

    heart_rates = json.loads(heart_rate_json)
    step_counts = json.loads(step_count_json)
    distance_records = json.loads(distance_json)
    sed_json = activity_level_dict["sedentary"]
    lightly_json = activity_level_dict["lightly"]
    fairly_json = activity_level_dict["fairly"]
    very_json = activity_level_dict["very"]
    inserting_set = []
    time_pair = dict()

    for one_day_hr in heart_rates["activities-heart"]:
        date = heart_rates["activities-heart"][0]["dateTime"]
        hr_array = heart_rates["activities-heart-intraday"]
        hr_dataset = hr_array["dataset"]
        if(len(hr_dataset) < 1):
            print("HR Dataset for selected date is empty.")
            if(int(step_counts["activities-steps"][0]["value"]) < 1):
                print("STEP Dataset for selected date is empty.")
                raise ValueError("Both HR and Step Dataset for selected date are empty.")
                return;

        for data in hr_dataset:
            user_id = uid
            dtstring = date + " " + data["time"]
            if(dtstring not in time_pair):
                time_pair[dtstring] = FitbitTimeSet(heart_rate=data["value"], step_count=0, activity_level=0, distance=0, uid=uid)
            else:
                time_pair[dtstring].heart_rate = data["value"]
        print("\t" + str(len(hr_dataset)) + " is the total heart rate timestamps in selected date: ")

    my_sum = 0

    for one_day_steps in step_counts["activities-steps"]:
        date = step_counts["activities-steps"][0]["dateTime"]
        hr_array = step_counts["activities-steps-intraday"]
        hr_dataset = hr_array["dataset"]
        for data in hr_dataset:
            my_sum += data["value"]
            if(data["value"] != 0):
                dtstring = date + " " + data["time"]
                if(dtstring not in time_pair):
                    time_pair[dtstring] = FitbitTimeSet(heart_rate=0, step_count=data["value"], activity_level=0, distance=0, uid=uid)
                else:
                    time_pair[dtstring].step_count = data["value"]


    print my_sum

    if(sed_json["activities-minutesSedentary"][0]["value"] != 0):
        date = sed_json["activities-minutesSedentary"][0]["dateTime"]
        for data in sed_json["activities-minutesSedentary-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 1

    if(lightly_json["activities-minutesLightlyActive"][0]["value"] != 0):
        date = lightly_json["activities-minutesLightlyActive"][0]["dateTime"]
        for data in lightly_json["activities-minutesLightlyActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 2

    if(fairly_json["activities-minutesFairlyActive"][0]["value"] != 0):
        date = fairly_json["activities-minutesFairlyActive"][0]["dateTime"]
        for data in fairly_json["activities-minutesFairlyActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 3

    if(very_json["activities-minutesVeryActive"][0]["value"] != 0):
        date = very_json["activities-minutesVeryActive"][0]["dateTime"]
        for data in very_json["activities-minutesVeryActive-intraday"]["dataset"]:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"];
                if(dtstring in time_pair):
                    time_pair[dtstring].activity_level += 4

    for one_day_distance in distance_records["activities-distance"]:
        date = distance_records["activities-distance"][0]["dateTime"]
        dist_array = distance_records["activities-distance-intraday"]
        dist_dataset = dist_array["dataset"]
        for data in dist_dataset:
            if(data["value"] != 0):
                dtstring = date + " " + data["time"]
                if(dtstring not in time_pair):
                    time_pair[dtstring] = FitbitTimeSet(heart_rate=0, step_count=0, activity_level=0, distance=data["value"], uid=uid)
                else:
                    time_pair[dtstring].distance = data["value"]

    print("\t...Done converting JSON data to dictionary")

    return time_pair

def combine_activity_levels(sedentary_payload, light_active_payload, fairly_active_payload, very_active_payload):
    print("Converting Activity Level JSON data to dictionary...")
    activity_level_dict = dict()
    if(sedentary_payload != ""):
        activity_level_dict["sedentary"] = json.loads(sedentary_payload)
    if(light_active_payload != ""):
        activity_level_dict["lightly"] = json.loads(light_active_payload)
    if(fairly_active_payload != ""):
        activity_level_dict["fairly"] = json.loads(fairly_active_payload)
    if(very_active_payload != ""):
        activity_level_dict["very"] = json.loads(very_active_payload)

    print("\t...Done Converting Activity Level JSON data to dictionary")

    return activity_level_dict

def flush_temp_db():
    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = "TRUNCATE TABLE Temp_Step_HeartRate"
        dbhandler.execute(stmt)

    except Exception as e:
        print "EXCEPTION IN flush_temp_db: " + str(e)

    finally:
        connection.commit()
        connection.close()

def insert_intraday_dict(time_pair):

    insert_set = []
    for time in time_pair:
        fitbit_data = time_pair[time]
        # print(str(time) + " / " + str(fitbit_data))
        insert_set.append((time, fitbit_data.uid, fitbit_data.heart_rate, fitbit_data.step_count, fitbit_data.distance, fitbit_data.activity_level, str(datetime.datetime.now())))

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        if(len(sys.argv) == 3):
            print "Inserting to Temp_Step_HeartRate DB."
            flush_user = insert_set[0][1]
            flush_date = insert_set[0][0][:10]
            # flush_date = str(datetime.date.today() - datetime.timedelta(days=7))
            print(datetime.date.today())
            print(flush_date)
            # stmt = "INSERT INTO Temp_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, distance, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            stmt = "DELETE FROM Temp_Step_HeartRate WHERE fitbit_uid = '%s' AND date(timestamp) = '%s'" % (flush_user, flush_date)
            dbhandler.execute(stmt)
            stmt = "INSERT INTO Temp_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, distance, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            dbhandler.executemany(stmt, insert_set)

        elif(len(sys.argv) == 4 and sys.argv[3] == "temp"):
            print "Inserting to Temp_Step_HeartRate DB."
            stmt = "INSERT INTO Temp_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, distance, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        elif(len(sys.argv) == 4 and sys.argv[3] == "pc"):
            print "Inserting to PC_Step_HeartRate DB."
            stmt = "INSERT INTO PC_Step_HeartRate (timestamp, fitbit_uid, heart_rate, step_count, distance, activity_level, added_on) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        else:
            print "INVALID SYSARGV. Exiting on insert phase."
            exit()

        if len(sys.argv) == 3:
            pass
        else:
            dbhandler.executemany(stmt, insert_set)

    except Exception as e:
        print "EXCEPTION IN insert_intraday_dict: " + str(e)

    finally:
        connection.commit()
        connection.close()

token = multi_login_routine()
