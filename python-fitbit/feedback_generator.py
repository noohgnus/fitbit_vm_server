#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################
#                                                          #
# Simple script to connect to a remote mysql database      #
#                                                          #
#                                                          #
# Install MySQLdb package by running:                      #
#                                                          #
#                       pip install MySQL-python           #
#                                                          #
############################################################

import json
import datetime
import MySQLdb as db
import MySQLdb.cursors
import traceback

import json
import fitbit
import requests
import base64
import sys


# Remote database info
HOST = "10.162.80.9"
PORT = 3306
USER = "fitbitter"
PASSWORD = "yiGLeVihDHhQMJPo"
DB = "mmcfitbit"

now_zero = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


class FeedbackData:
    def __init__(self, patient_id, fitbit_uid, week=-1, avg_weight=-1, avg_steps=-1, total_active_mins=-1, height=-1):
        self.patient_id = patient_id
        self.fitbit_uid = fitbit_uid
        self.week = week
        self.avg_weight = avg_weight
        self.avg_steps = avg_steps
        self.total_active_mins = total_active_mins
        self.height = height

    def __repr__(self):
        return "FeedbackData(User " + str(self.patient_id) + ',' + str(self.fitbit_uid) + ', week: ' + str(self.week) \
               + ', avg_weight: ' + str(self.avg_weight) + ', avg_steps: ' + self.uid + ")"


def read_from_db():

    try:
        connection = db.Connection(host=HOST, port=PORT, user=USER, passwd=PASSWORD, db=DB,
                                   cursorclass=MySQLdb.cursors.SSCursor)

        user_cursor = connection.cursor(db.cursors.DictCursor)
        # user_cursor = connection.cursor()
        user_cursor.execute("SELECT * FROM PC_Users")
        update_ids = dict()
###############################
# GET WHICH USER TO UPDATE
###############################
        for row in user_cursor:
            if row["last_feedback"] < now_zero - datetime.timedelta(days=7) and row["week"] <= 5:
                print(row['notes'])
                update_ids[row["user_id"]] = row["fitbit_uid"]

###############################
# GENERATE NEW FEEDBACK DATA
###############################
        kv_pair = []

        for user_key in update_ids:
            kv_pair.append((update_ids[user_key], str(datetime.datetime.now() - datetime.timedelta(days=7))))
        stmt = "SELECT * FROM PC_Step_HeartRate WHERE fitbit_uid=%s AND timestamp>%s"
        user_cursor.executemany(stmt, kv_pair)

        user_step_set = dict()
        user_activity_set = dict()
        for row in user_cursor:
            # Getting total active mins of lvl 3 and 4
            if row["activity_level"] >= 3:
                if user_activity_set.get(row["fitbit_uid"]) is None:
                    user_activity_set[row["fitbit_uid"]] = 0
                user_activity_set[row["fitbit_uid"]] += 1

            # Generating daily total step counts in a nested dict
            if user_step_set.get(row["fitbit_uid"]) is None:
                user_step_set[row["fitbit_uid"]] = {row["timestamp"]: row["step_count"]}
            else:
                if user_step_set[row["fitbit_uid"]].get(row["timestamp"].date()) is None:
                    user_step_set[row["fitbit_uid"]][row["timestamp"].date()] = row["step_count"]
                else:
                    user_step_set[row["fitbit_uid"]][row["timestamp"].date()] += row["step_count"]
            # print(row)

        # print(user_step_set)
        print(user_activity_set)
###############################
# UPDATE FEEDBACK TABLE
###############################
        for user_id in update_ids:
            user_cursor.execute("UPDATE PC_Users SET \
                last_feedback='%s' WHERE user_id='%s'" % (datetime.datetime.now(), user_id))
            user_cursor.execute("UPDATE PC_Users SET week=week+1 WHERE user_id='%s'" % user_id)
            user_cursor.execute("INSERT INTO PC_Feedback \
                    (patient_id, fitbit_uid, week, avg_weight, avg_steps, total_active_mins, height, added_on) \
                    VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                    % ('1', '5T82TY', '1', '1', '1', '1', '1', str(datetime.datetime.now())))

        connection.commit()
        connection.close()
    except Exception as e:
        traceback.print_exc()


def temp():
    try:
        connection = db.Connection(host=HOST, port=PORT,
                                   user=USER, passwd=PASSWORD, db=DB,
                                   cursorclass=MySQLdb.cursors.SSCursor
                                   )

        cursor = connection.cursor(db.cursors.DictCursor)
        result = cursor.execute("SELECT * FROM PC_Step_HeartRate")
        # now_time = str(datetime.datetime.now())
        # print(now_time)
        # rows = cursor.fetchall()
        print(result.fetchall())

        # for device_id in device_id_pair:
        #     # print(row["submitted_at"] < datetime.datetime.now())
        #     print("DEVICE : " + device_id)
        #     device = device_id_pair[device_id]
        #     result = cursor.execute("INSERT INTO PC_Devices \
        #         (fitbit_uid, device_id, last_sync_time, device_version, device_type, battery, battery_level, updated_at)\
        #         VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')\
        #         ON DUPLICATE KEY UPDATE last_sync_time='%s', battery='%s', battery_level='%s', updated_at='%s'"
        #                             % (device.uid, device_id, device.last_sync_time, device.device_version,
        #                                device.device_type, device.battery, device.battery_level, now_time,
        #                                device.last_sync_time, device.battery, device.battery_level, now_time))
    except Exception as e:
        print("Exception")
        print(e)

    else:
        # cursor.close()
        connection.commit()
        connection.close()


read_from_db()

