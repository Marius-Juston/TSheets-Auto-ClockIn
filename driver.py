import os

from stored_data import TSheetsCache
from tsheets_retriever import TSheetsAPI

if __name__ == '__main__':
    with TSheetsCache() as database:
        token = os.environ['TSHEETS_TOKEN']

        tsheets_api = TSheetsAPI(token)

        if database.needs_update(database.users_table):
            users = tsheets_api.user_to_list()
            success = database.insert_users(users)
            database.add_time_stamp(database.users_table, success)

        if database.needs_update(database.jobcodes_table):
            jobcodes = tsheets_api.jobcodes_to_list()
            success = database.insert_jobcodes(jobcodes)
            database.add_time_stamp(database.jobcodes_table, success)

        # Use database.get_users() to get all users
        user = "Marius Juston"

        # Use database.get_jobs() to get all jobs
        job = "Programming"

        user_id = database.name_to_id(user)

        if user_id is None:
            raise ValueError(f"The user name {user} does not exist.")

        jobcode_id = database.job_to_jobcode_id(job)

        if jobcode_id is None:
            raise ValueError(f"The job {job} does not exist.")

        clock_in_response = tsheets_api.clock_in(user_id, jobcode_id)

        # This will allow you to know who is currently clocked in
        user_ids = tsheets_api.get_clocked_in_users()
        names = database.user_ids_to_names(user_ids)
        print(names)
