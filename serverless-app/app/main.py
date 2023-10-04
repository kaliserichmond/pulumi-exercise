from flask import jsonify
import functions_framework
# import os

# from google.cloud.sql.connector import Connector, IPTypes
# import pymysql

# import sqlalchemy

@functions_framework.http
def data(request):

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
    }

    if request.method == "OPTIONS":
        return "", 204, headers

    # TODO: get the data from the request
    # data = request.data


    headers["Content-Type"] = "application/json"
    return jsonify({"refresh": data}), 200, headers

@functions_framework.cloud_event
def exercise_handler(cloud_event):
    #TODO: take the new storage object and index to the database

#example from https://cloud.google.com/sql/docs/mysql/connect-functions
# def connect_with_connector() -> sqlalchemy.engine.base.Engine:
#     """
#     Initializes a connection pool for a Cloud SQL instance of MySQL.

#     Uses the Cloud SQL Python Connector package.
#     """
#     # Note: Saving credentials in environment variables is convenient, but not
#     # secure - consider a more secure solution such as
#     # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
#     # keep secrets safe.

#     instance_connection_name = os.environ[
#         "INSTANCE_CONNECTION_NAME"
#     ]  # e.g. 'project:region:instance'
#     db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
#     db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
#     db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

#     ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

#     connector = Connector(ip_type)

#     def getconn() -> pymysql.connections.Connection:
#         conn: pymysql.connections.Connection = connector.connect(
#             instance_connection_name,
#             "pymysql",
#             user=db_user,
#             password=db_pass,
#             db=db_name,
#         )
#         return conn

#     pool = sqlalchemy.create_engine(
#         "mysql+pymysql://",
#         creator=getconn,
#         # ...
#     )
#     return pool
