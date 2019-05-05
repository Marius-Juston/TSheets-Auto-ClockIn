import sqlite3


class TSheetsCache:
    users_table = 'users'
    jobcodes_table = 'jobcodes'
    time_stamp_table = 'info_timestamp'

    __update_rates = {
        users_table: 100,
        jobcodes_table: 100,
    }

    def __init__(self, database_file="tsheets_info.db", update_rates: dict = None) -> None:
        super().__init__()

        self.conn = sqlite3.connect(database_file)
        self.cursor = self.conn.cursor()

        if update_rates is not None:
            self.__update_rates = update_rates

        self.create_timestamp_table()
        self.create_username_table()
        self.create_jobcodes_table()

    def table_exists(self, table):
        try:
            self.cursor.execute('''SELECT 1 FROM {} LIMIT 1;'''.format(table))
            return True
        except sqlite3.OperationalError:
            return False

    def create_username_table(self):
        if not self.table_exists(self.users_table):
            self.cursor.execute("CREATE TABLE users (user_id INTEGER NOT NULL PRIMARY KEY, name text, email text) ")
            self.conn.commit()

    def create_jobcodes_table(self):
        if not self.table_exists(self.jobcodes_table):
            self.cursor.execute('''CREATE TABLE jobcodes 
                                    (
                                    jobcode_id INTEGER NOT NULL PRIMARY KEY, 
                                    parent_id INTEGER NOT NULL ,
                                    name TEXT,
                                    FOREIGN KEY (parent_id) 
                                        REFERENCES jobcodes(jobcode_id) 
                                    )''')
            self.conn.commit()

    def create_timestamp_table(self):
        if not self.table_exists(self.time_stamp_table):
            self.cursor.execute("CREATE TABLE info_timestamp (table_name text, time_stamp TIMESTAMP,successful BOOL )")
            self.conn.commit()

    def names_to_id(self, names):
        data = {}

        for name in names:
            data[name[0]] = {'user_id': self.name_to_id(name)}

        return data

    def user_id_to_name(self, user_id):
        if type(user_id) == int:
            user_id = (user_id,)

        result = self.cursor.execute("SELECT name from users where user_id==? LIMIT 1", user_id)
        result = result.fetchone()

        if result is None:
            return result

        return result[0]

    def user_ids_to_names(self, user_ids):
        return [self.user_id_to_name(user_id) for user_id in user_ids]

    def name_to_id(self, name):
        if type(name) == str:
            name = (name,)

        result = self.cursor.execute("SELECT users.user_id from users where name==? LIMIT 1", name)
        result = result.fetchone()

        if result is None:
            return result

        return result[0]

    def job_to_jobcode_id(self, job):
        if type(job) == str:
            job = (job,)

        result = self.cursor.execute("SELECT jobcode_id from jobcodes where name==? LIMIT 1", job)
        result = result.fetchone()

        if result is None:
            return result

        return result[0]

    def get_users(self):
        result = self.cursor.execute("SELECT name from users")
        return list(map(lambda x: x[0], result.fetchall()))

    def add_time_stamp(self, tables, successful):
        # if isinstance(tables, str):
        #     tables = ((tables,),)

        self.cursor.executemany("INSERT INTO info_timestamp VALUES (?, CURRENT_TIMESTAMP, ?)", [[tables, successful]])
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def delete_information(self, table):
        self.cursor.execute("DELETE FROM {}".format(table))
        self.conn.commit()

    def insert_users(self, users, purge_table=True):
        try:
            if purge_table:
                self.delete_information(self.users_table)

            self.cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", users)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            return False

    def insert_jobcodes(self, jobcodes, purge_table=True):
        try:
            if purge_table:
                self.delete_information(self.jobcodes_table)

            self.cursor.executemany("INSERT INTO jobcodes VALUES (?, ?, ? )", jobcodes)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(e)
            return False

    def needs_update(self, table_name: str):
        # if isinstance(table_names, str):
        #     table_names = (table_names,)

        time = self.__update_rates[table_name]

        a = self.cursor.execute(
            '''SELECT time_stamp
                from info_timestamp
                where (
                          successful
                          AND table_name = ?
                          AND (JULIANDAY('now') - JULIANDAY(time_stamp)) <= ?
                        )
                ORDER BY time_stamp DESC LIMIT 1''',
            [table_name, time])

        a = a.fetchone()

        return a is None

    def get_jobs(self):
        result = self.cursor.execute("SELECT name from jobcodes")
        return list(map(lambda x: x[0], result.fetchall()))


if __name__ == '__main__':
    with TSheetsCache() as database:
        print(database.get_users())
        print(database.get_jobs())
