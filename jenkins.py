#!/usr/bin/python3

import datetime
import jenkinsapi
import requests
import sqlite3

from sqlite3 import Error
from jenkinsapi.jenkins import Jenkins

# Dict defining jenkins different build status. Could be moved to DB to avoid hard coding
build_status = {'SUCCESS': 1, 'FAILURE': 2, 'NOT_BUILT': 3, 'UNSTABLE': 4, 'ABORTED': 5}


# ------------------ DB connection and access functions ---------------------#

# Create DB connection
def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


# Check if job exists
def job_exists(conn, job_name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE job_name=?", (job_name,))
    data = cur.fetchone()
    if data is not None:
        return True
    return False


"""
This function checks whether a job exists.
If job exists, it updates the details
else it saves the job as a fresh entry
Note: I used job_name as the identifier, so I made it unique in the db
A better solution would be to use an id/build_id
"""
def save_job_details(conn, server):
    cur = conn.cursor()
    for j in server.get_jobs():
        job_instance = server.get_job(j[0])

        status = get_job_build_status(job_instance)

        last_checked = datetime.datetime.now()

        job_detail = (status, last_checked, job_instance.name)

        exists = job_exists(conn, job_instance.name)

        if exists:
            sql = "UPDATE jobs set status=?, last_checked=? WHERE job_name=?"
        else:
            sql = "INSERT INTO jobs (status, last_checked, job_name) VALUES (?, ?, ?)"
        with conn:
            cur.execute(sql, job_detail)
            conn.commit()
    conn.close()


# ----------------------Jenkins Access functions -----------------------------#

# Get server instance
def get_server_instance():
    jenkins_url = 'http://localhost:8080'
    try:
        server = Jenkins(jenkins_url, username='emeka', password='Ea#$gle22!')
    except requests.exceptions.HTTPError:
        print("Could not connect to server. Please verify that your credentials are correct.")
        server = None
    return server


# Get job build status
def get_job_build_status(job_instance):
    try:
        status = job_instance.get_last_build().get_status()
    except jenkinsapi.custom_exceptions.NoBuildData:
        status = 'NOT_BUILT'

    return build_status[status]


def main():
    database = "/var/www/html/py_script.sqlite3"

    # create a database connection
    conn = create_connection(database)

    server = get_server_instance()

    if server is not None:
        save_job_details(conn, server)


if __name__ == '__main__':
    main()
