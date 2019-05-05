import datetime
import os
# import pandas as pd
import time

import requests


def get(url, filters=None, header=None):
    response = requests.api.get(url, params=filters, headers=header)
    response.raise_for_status()

    return response


def post(url, data=None, json=None, header=None):
    response = requests.api.post(url, data=data, json=json, headers=header)
    response.raise_for_status()

    return response


class TSheetsAPI:

    def __init__(self, tsheets_token, group_names=("Students",)) -> None:
        super().__init__()
        self.auth_options = {"Authorization": "Bearer {}".format(tsheets_token)}
        self.group_names = group_names

        self.groups_url = "https://rest.tsheets.com/api/v1/groups"
        self.users_url = "https://rest.tsheets.com/api/v1/users"
        self.timesheets_url = 'https://rest.tsheets.com/api/v1/timesheets'
        self.jobcodes_url = 'https://rest.tsheets.com/api/v1/jobcodes'
        self.notifications_url = 'https://rest.tsheets.com/api/v1/notifications'

        self.group_ids = None

    def get(self, url, filters=None):
        return get(url, filters, header=self.auth_options)

    def post(self, url, data=None, json=None):
        return post(url, data=data, json=json, header=self.auth_options)

    def get_group_ids(self):
        group_filter = {
            "names": ",".join(self.group_names),
            "supplemental_data": "no"
        }

        group_ids = self.get(self.groups_url, group_filter).json()
        group_ids = tuple(group_ids["results"]["groups"])

        return group_ids

    def get_users(self):
        if self.group_ids is None:
            self.group_ids = self.get_group_ids()

        user_filters = {
            "supplemental_data": "no"
        }

        if self.group_ids is not None:
            user_filters["group_ids"] = ",".join(self.group_ids)

        users = self.get(self.users_url, filters=user_filters)
        return users.json()["results"]["users"]

    def user_to_list(self):
        users = self.get_users()
        data = []

        for key, value in users.items():
            name = " ".join([value["first_name"], value["last_name"]])
            email_address = value['email']
            data.append([key, name, email_address])

        return data

    def get_jobcodes(self):

        jobcode_filters = {
            "supplemental_data": "no"
        }

        data = {}

        page_number = 1
        while True:
            jobcode_filters["page"] = page_number

            users = self.get(self.jobcodes_url, filters=jobcode_filters)
            response = users.json()["results"]["jobcodes"]

            if not response:
                break
            else:
                print(page_number)
                page_number += 1
                data.update(response)

        return data

    def jobcodes_to_list(self):
        jobcodes = self.get_jobcodes()
        data = []

        for value in jobcodes.values():
            id = value["id"]
            parent_id = value["parent_id"]
            name = value["name"]

            data.append([id, parent_id, name])

        return data

    def clock_in(self, id, job_code):
        start_time = get_current_time()

        payload = f"""{{
            "data": [
                    {{
                        "user_id": {id},
                        "jobcode_id": {job_code},
                        "type": "regular",
                        "start": "{start_time}",
                        "end": ""
                    }}
                ]
            }}"""

        clock_in_response = self.post(self.timesheets_url, data=payload).json()
        clock_in_response = clock_in_response['results']['timesheets']

        for timesheet in clock_in_response:
            if clock_in_response[timesheet]['_status_code'] >= 400:
                raise ValueError({timesheet: clock_in_response[timesheet]})

    def get_clocked_in_users(self):

        clocked_in_filter = {
            "user_ids": None,
            "supplemental_data": "no",
            "on_the_clock": "yes",
            "per_page": 1,
            "start_date": (datetime.datetime.now() - datetime.timedelta(weeks=52)).strftime("%Y-%m-%d")
        }
        user_ids = []

        for user in self.get_users():
            user = int(user)
            clocked_in_filter['user_ids'] = user

            result = self.get(self.timesheets_url, clocked_in_filter)
            result = result.json()['results']['timesheets']

            if len(result) != 0:
                user_ids.append(user)

        return user_ids


def get_current_time():
    # Calculate the offset taking into account daylight saving time
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    return datetime.datetime.now().replace(microsecond=0, tzinfo=datetime.timezone(offset=utc_offset)).isoformat()


if __name__ == '__main__':
    token = os.environ['TSHEETS_TOKEN']

    tsheets_api = TSheetsAPI(token)
    tsheets_api.get_users()
