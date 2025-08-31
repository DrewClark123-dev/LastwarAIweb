import pandas as pd
import mysql.connector
import sqlite3

def create_connection(database):
    try:
        if database == 'mySQL':
            connection = mysql.connector.connect(
                host="localhost",
                user="DrewC125",
                password="1103",
                database="lastwar"
            )
            if connection.is_connected():
                print(f"[INFO] Connected to {database} database")
                return connection
        else:
            connection = sqlite3.connect("lastwar.sqlite")  # sqlite
            print(f"[INFO] Connected to {database} database")
            return connection
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def disconnect(connection):
    connection.close()
    print("[INFO] Connection closed")

def query_df(conn, query, parms=()):
    cursor = conn.cursor()
    cursor.execute(query, parms)
    results = cursor.fetchall()
    df = pd.DataFrame(results)
    cursor.close()
    return df