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
    def __init__(self, fitbit_uid, patient_id="NOT_SUPPLIED", week=-1, avg_weight=-1, avg_steps=-1, total_active_mins=-1, height=-1):
        self.patient_id = patient_id
        self.fitbit_uid = fitbit_uid
        self.week = week
        self.avg_weight = avg_weight
        self.avg_steps = avg_steps
        self.total_active_mins = total_active_mins
        self.height = height

    def __repr__(self):
        return "FeedbackData(User: " + str(self.patient_id) + ', fitbit_uid: ' + str(self.fitbit_uid) + ', week: ' + str(self.week) \
               + ', avg_weight: ' + str(self.avg_weight) + ', avg_steps: ' + str(self.avg_steps) \
               + ", total_active_mins: " + str(self.total_active_mins)


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
                update_ids[row["fitbit_uid"]] = {"user_id": row["user_id"], "week": row["week"]}

###############################
# RETRIEVE UPDATABLE INNER JOINED ROWS FROM DB
###############################

        join_cursor = connection.cursor(db.cursors.DictCursor)
        join_cursor.execute("""SELECT * FROM PC_Users INNER JOIN PC_Step_HeartRate ON PC_Step_HeartRate.timestamp > '%s'
            AND PC_Users.fitbit_uid = PC_Step_HeartRate.fitbit_uid
            AND PC_Users.last_feedback < '%s' AND PC_Users.week <= 5"""
                            % (str(now_zero - datetime.timedelta(days=7)), str(now_zero - datetime.timedelta(days=1))))
        weight_cursor = connection.cursor(db.cursors.DictCursor)
        weight_cursor.execute("""SELECT * FROM PC_Weight WHERE timestamp > '%s' 
            """ % str(now_zero - datetime.timedelta(days=30)))

###############################
# GENERATE NEW FEEDBACK DATA
###############################
        feedback_dict = dict()
        user_weight_set = dict()
        for row in weight_cursor:
            # print(row)
            if user_weight_set.get(row["fitbit_uid"]) is None:
                user_weight_set[row["fitbit_uid"]] = {row["timestamp"].date(): row["weight"]}
            else:
                user_weight_set[row["fitbit_uid"]][row["timestamp"].date()] = row["weight"]

        for key in user_weight_set:
            weigh_in_num = len(user_weight_set[key])
            weight_list = user_weight_set[key].values()
            total_weight = 0
            for w in weight_list:
                total_weight += w
            avg_weight = total_weight / weigh_in_num
            user_weight_set[key]["avg_weight"] = avg_weight


        print(user_weight_set)

        user_step_set = dict()
        user_activity_set = dict()

        for row in join_cursor:
            # print(row)
            # Getting total active mins of lvl 3 and 4
            if row["activity_level"] >= 3:
                if user_activity_set.get(row["fitbit_uid"]) is None:
                    user_activity_set[row["fitbit_uid"]] = 0
                user_activity_set[row["fitbit_uid"]] += 1
                # print("increment " + str(row["fitbit_uid"]) + " / " + str(row["timestamp"]))

            # Generating daily total step counts in a nested dict
            if user_step_set.get(row["fitbit_uid"]) is None:
                user_step_set[row["fitbit_uid"]] = {row["timestamp"].date(): row["step_count"]}
            else:
                if user_step_set[row["fitbit_uid"]].get(row["timestamp"].date()) is None:
                    user_step_set[row["fitbit_uid"]][row["timestamp"].date()] = row["step_count"]
                else:
                    user_step_set[row["fitbit_uid"]][row["timestamp"].date()] += row["step_count"]
            # print(row)



        ################################
        # Calculate averages
        ################################
        for key in user_step_set:
            steps_list = user_step_set[key].values()
            count = 0
            total_steps = 0;
            for step in steps_list:
                if step > 0:
                    count += 1
                    total_steps += step
            avg_steps = total_steps / count
            user_step_set[key]["avg_steps"] = avg_steps

            ###################
            # add avg step feature to feedback obj
            ###################
            if total_steps > 0:
                if feedback_dict.get(key) is None:
                    feedback_dict[key] = FeedbackData(fitbit_uid=key, avg_steps=avg_steps)
                else:
                    feedback_dict[key].avg_steps = avg_steps

        print(user_step_set)
        print("###")
        print(user_activity_set)
        print("###")

        ###################
        # add total active mins feature to feedback obj
        ###################

        for key in user_activity_set:
            print("acti set enter")
            if user_activity_set[key] > 0:
                if feedback_dict.get(key) is None:
                    print("acti set true")

                    feedback_dict[key] = FeedbackData(fitbit_uid=key, total_active_mins=user_activity_set[key])
                else:
                    print("acti set else")
                    feedback_dict[key].total_active_mins = user_activity_set[key]


        ###################
        # add avg weight feature to feedback obj
        ###################

        for key in user_weight_set:
            if user_weight_set[key]["avg_weight"] > 0:
                if feedback_dict.get(key) is None:
                    feedback_dict[key] = FeedbackData(fitbit_uid=key, avg_weight=user_weight_set[key]["avg_weight"])
                else:
                    feedback_dict[key].avg_weight = user_weight_set[key]["avg_weight"]


        ################################
        # Prepare Feedback obj
        ################################
        print(feedback_dict)

        for key in feedback_dict:
            feedback_dict[key].patient_id = update_ids[key]["user_id"]
            feedback_dict[key].week = update_ids[key]["week"]

###############################
# UPDATE FEEDBACK TABLE
###############################
        insert_set = []
        for key in feedback_dict:
            fb = feedback_dict[key]
            insert_set.append((fb.patient_id, fb.fitbit_uid, fb.week, fb.avg_weight, fb.avg_steps,
                               fb.total_active_mins, fb.height, str(datetime.datetime.now())))

        # for user_id in update_ids:
            ################################################################
            # ENABLE FOR PROD
            ################################################################
            # user_cursor.execute("UPDATE PC_Users SET \
            #     last_feedback='%s' WHERE user_id='%s'" % (datetime.datetime.now(), user_id))
            # user_cursor.execute("UPDATE PC_Users SET week=week+1 WHERE user_id='%s'" % user_id)

        print(insert_set)

        insert_cursor = connection.cursor()

        stmt = "INSERT INTO PC_Feedback \
                        (patient_id, fitbit_uid, week, avg_weight, avg_steps, total_active_mins, height, added_on) \
                        VALUES ('%s', %s, '%s', '%s', '%s', '%s', '%s', %s)"

        insert_cursor.executemany(stmt, insert_set)

        connection.commit()
        connection.close()
    except Exception as e:
        traceback.print_exc()
        # if insert_cursor is not None:
        #     print(insert_cursor._last_executed)


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

