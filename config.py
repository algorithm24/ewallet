import psycopg2
import enum
from functools import wraps

# CONFIG DATABASE

DB_NAME = 'test2'
HOST = "localhost"
USER = "admin"
PASSWORD = "T3ch4GFT!2345"

def get_db_config():
    return DB_NAME, HOST, USER, PASSWORD

def set_up_db_connection(db_name=DB_NAME, host=HOST, user=USER, password=PASSWORD):
    conn = psycopg2.connect(host=host,
                            database=db_name,
                            user=user,
                            password=password,
                            port=5432)
    return conn

def connect():
    conn = set_up_db_connection()
    return conn, conn.cursor()

def close_connection(con,cur):
    cur.close()
    con.close()

def create_table_merchant(connection, cursor):
    table_name = 'merchants'
    sql_str = f"""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE TABLE IF NOT EXISTS {table_name} (
                merchant_id uuid DEFAULT uuid_generate_v4 (),
                merchant_url VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL UNIQUE,
                api_key uuid DEFAULT uuid_generate_v4 (),
                PRIMARY KEY (merchant_id))"""
    cursor.execute(sql_str)
    connection.commit()

def create_table_account(connection, cursor):
    table_name = 'accounts'
    sql_str = f"""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE TABLE IF NOT EXISTS {table_name} (
                account_id uuid DEFAULT uuid_generate_v4 (),
                type Type_Enum NOT NULL,
                balance FLOAT NOT NULL,
                merchant_id uuid,
                PRIMARY KEY (account_id),
                CONSTRAINT fk_merchant FOREIGN KEY(merchant_id) REFERENCES merchants(merchant_id))"""
    cursor.execute(sql_str)
    connection.commit()

def create_table_transaction(connection, cursor):
    table_name = 'transactions'
    sql_str = f"""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                CREATE TABLE IF NOT EXISTS {table_name} (
                transaction_id uuid DEFAULT uuid_generate_v4 (),
                account_income_id uuid,
                account_outcome_id uuid,
                status Status_Enum NOT NULL,
                signature VARCHAR(255),
                amount FLOAT NOT NULL,
                extra_data VARCHAR(255) NOT NULL,
                merchant_id uuid,)"""

    cursor.execute(sql_str)
    connection.commit()

def execute_query(connection, cursor, query_str):
    cursor.execute(query_str)
    connection.commit()
    if cursor.description == None:
        return None
    else:
        result = cursor.fetchall()
        return result

def is_table_existed(connection, cursor, table_name):
    query_str = f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table_name}');"
    is_existed = execute_query(connection, cursor, query_str)[0][0]
    return is_existed

def data_type():
    connection, cursor = connect()
    try:
        cursor.execute('''CREATE TYPE Type_Enum as ENUM(
                        'personal',
                        'merchant',
                        'issuer')''')
        cursor.execute('''CREATE TYPE Status_Enum as ENUM(
                        'INITIALIZED',
                        'CONFIRMED',
                        'VERIFIED',
                        'COMPLETED',
                        'CANCELED',
                        'EXPIRED',
                        'FAILED')''')
        print('Datatype created')
        connection.commit()
    except:
        print('Datatype exited')


import signal

class TimeoutError(Exception):
    def __init__(self, value = "Timed Out"):
        self.value = value
    def __str__(self):
        return repr(self.value)

def timeout(seconds_before_timeout):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutError()
        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result
        return new_f
    return decorate