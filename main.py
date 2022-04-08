from multiprocessing import connection
import socketserver
import config
import service
from api_handler import APIHandler
import psycopg2

if __name__ == "__main__":
    # http part
    try:
        connection,cursor = config.connect()
        PORT = 8000
        # Create an object of the above class
        my_server = socketserver.TCPServer(("0.0.0.0", PORT), APIHandler)
        # Star the server
        print(f"Server started at {PORT}")
        my_server.serve_forever()
    except (Exception, psycopg2.Error) as error:
        print("Error while processing data from PostgreSQL", error)
    finally:
        config.close_connection(connection,cursor)
        print("Close connection")
    # database part
    # connection,cursor = config.connect()   
    # config.data_type() 
    # if cursor == None:
    #     print("\nConnect failed!\n")
    # else:
    #     print("\nConnect successfully!\n")
    #     print("Checking for creating tables")
    #     config.create_table_merchant(connection,cursor)
    #     config.create_table_account(connection,cursor)
    #     config.create_table_transaction(connection,cursor)
