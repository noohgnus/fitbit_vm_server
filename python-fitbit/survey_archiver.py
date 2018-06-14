#!/usr/bin/env python
import json
import datetime
import MySQLdb as db

import json
import fitbit
import requests
import base64
import sys
import re
import pytz
from dateutil import tz

EST_TZ = pytz.timezone("US/Eastern")
from_zone = tz.gettz('UTC')
to_zone = tz.gettz('America/New_York')
#Remote database info
HOST = "10.162.80.9"
PORT = 3306
USER = "fitbitter"
PASSWORD = "yiGLeVihDHhQMJPo"
DB = "mmcfitbit"

now = str(datetime.datetime.now())

class SurveyData:
    def __init__(self, uid, survey_string, submitted_at):
        self.uid = uid
        self.survey_string = survey_string
        self.submitted_at = submitted_at

    def __repr__(self):
        return "SurveyData(User: " + str(self.uid) + ', submitted_at: ' + str(self.submitted_at) + ', survey: ' + str(self.survey_string) + ")"

def main():
    survey_set = pull_yesterday_survey()
    calculate_category_scores(survey_set[0].survey_string)
    # insert_surveys(survey_set)

def pull_yesterday_survey():
    print("Retrieving surveys from yesterday...")
    r = requests.get("http://localhost:8000/polls/get_surveys_yesterday/")
    print(r.text)

    survey_json = json.loads(r.text)
    survey_list = []
    surveys = survey_json["Surveys"]
    for survey in surveys:
        survey_time = survey["submit_time"]
        if '.' not in survey_time:
            survey_time = survey_time[:-1] + ".000Z"
        utc = datetime.datetime.strptime(survey_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc = utc.replace(tzinfo=from_zone)
        # Convert time zone
        est = utc.astimezone(to_zone).strftime("%Y-%m-%d %H:%M:%S")
        print est

        survey_list.append(SurveyData(uid=survey["submit_user_id"], survey_string=survey["answer_sequence"], submitted_at=est))

    # print(uid)
    print(survey_list)
    print("\t...Done getting yesterday's surveys")

    return survey_list

def calculate_category_scores(survey_string):
    def recode_choices(answer_map):
        recode_type_one = [1, 2, 20, 22, 34, 36]
        recode_type_two = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        recode_type_three = [13, 14, 15, 16, 17, 18, 19]
        recode_type_four = [21, 23, 26, 27, 30]
        recode_type_five = [24, 25, 28, 29, 31]
        recode_type_six = [32, 33, 35]

        for q in recode_type_one:
            answer_map[q] = 25 * (5 - answer_map[q])
        for q in recode_type_two:
            answer_map[q] =50 * (answer_map[q] - 1)
        for q in recode_type_three:
            answer_map[q] = 100 * (answer_map[q] - 1)
        for q in recode_type_four:
            answer_map[q] = 20 * (6 - answer_map[q])
        for q in recode_type_five:
            answer_map[q] = 20 * (answer_map[q] - 1)
        for q in recode_type_six:
            answer_map[q] = 25 * (answer_map[q] - 1)
        return answer_map

    def weigh_categories(ra):
        avg_map = dict()
        avg_map["physical_functioning"] = (ra[3] + ra[4] + ra[5] + ra[6] + ra[7] + ra[8] + ra[9] + ra[10] + ra[11] + ra[12]) / float(10)
        avg_map["role_limited_physical"] = (ra[13] + ra[14] + ra[15] + ra[16]) / float(4)
        avg_map["role_limited_physical"] = (ra[17] + ra[18] + ra[19]) / float(3)
        avg_map["energy"] = (ra[23] + ra[27] + ra[29] + ra[31]) / float(4)
        avg_map["emotional_wellbeing"] = (ra[24] + ra[25] + ra[26] + ra[28] + ra[30]) / float(5)
        avg_map["social_functioning"] = (ra[20] + ra[32]) / float(2)
        avg_map["pain"] = (ra[21] + ra[22]) / float(2)
        avg_map["general_health"] = (ra[1] + ra[33] + ra[34] + ra[35] + ra[36]) / float(5)
        return avg_map

    answer_map = dict()
    count = 1
    for i in survey_string:
        answer_map[count] = int(i)
        count += 1




    recoded_answers = recode_choices(answer_map)
    print(recoded_answers)

    weighted_map = weigh_categories(recoded_answers)
    return 

def pull_checkins_survey():
    pass


def insert_surveys(survey_set):
    insert_set = []
    for survey in survey_set:
        dataset = list(survey.survey_string)
        # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        insert_set.append((survey.uid, survey.submitted_at, str(datetime.datetime.now())) + tuple(dataset))
        print(insert_set)

    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()
        stmt = "INSERT INTO PC_Surveys_QoL (user_id, submitted_at, added_on, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14, q15, q16, q17, q18, q19, q20, q21, q22, q23, q24, q25, q26, q27, q28, q29, q30, q31, q32, q33, q34, q35, q36) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        dbhandler.executemany(stmt, insert_set)


    except Exception as e:
        print "EXCEPTION IN insert_surveys: " + str(e)

    finally:
        connection.commit()
        connection.close()

main()
# calculate_category_scores("322332899")

