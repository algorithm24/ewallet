import functools
import http.server
from pkgutil import get_data
from functools import wraps
import socketserver
import json
from typing import Tuple
from http import HTTPStatus
import config
import service
import os
from urllib.parse import urlparse
from urllib.parse import parse_qs

PORT = 8000

class APIHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)

    # def token_required(self):
    #     def decorate(f):
    #         def new_f(*args, **kwargs):
    #             token = self.headers['Authorization']
    #             if not token:
    #                 return {"messenger":"need token"}
    #             return f(*args, **kwargs)
    #         return new_f
    #     return decorate

    def do_GET(self):
        if self.path.find('account') != -1 and self.path.find('token') != -1:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/text")
            self.end_headers()
            parsed_url = self.path.split('/')
            account_id = parsed_url[2]
            output_data,code = service.get_token(account_id)
            self.wfile.write(output_data.encode('utf-8'))

    
    def do_POST(self):

        if self.path == '/merchant/signup':
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            output_data,code = service.signup_merchant(connection,cursor,data)
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))
        
        elif self.path == '/account':
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            output_data,code = service.new_account(connection,cursor,data)
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))

        elif self.path.find('account') != -1 and self.path.find('topup') != -1:
            token = self.headers['Authorization']
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            issuer_accound_id = service.decode_token(token)['account_id']
            output_data,code = service.topup(connection,cursor,data,issuer_accound_id)
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))
        
        elif self.path == '/transaction/create':
            token = self.headers['Authorization']
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            merchant_account_id = service.decode_token(token)['account_id']
            output_data,code = service.transaction_create(connection,cursor,data,merchant_account_id)
            output_json = json.dumps(output_data)
            self.wfile.write(output_json.encode('utf-8'))

        elif self.path == '/transaction/confirm':
            token = self.headers['Authorization']
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            personal_account_id = service.decode_token(token)['account_id']
            try:
                output_data,code = service.transaction_confirm(connection,cursor,personal_account_id,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
            except:
                output_data,code = service.transaction_expired(connection,cursor,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

        elif self.path == '/transaction/verify':
            token = self.headers['Authorization']
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            personal_account_id = service.decode_token(token)['account_id']
            try:
                output_data,code = service.transaction_verify(connection,cursor,personal_account_id,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
            except:
                output_data,code = service.transaction_expired(connection,cursor,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))

        elif self.path == '/transaction/cancel':
            token = self.headers['Authorization']
            data = self.get_data()
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            connection, cursor = config.connect()
            personal_account_id = service.decode_token(token)['account_id']
            try:
                output_data,code = service.transaction_cancel(connection,cursor,personal_account_id,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
            except:
                output_data,code = service.transaction_expired(connection,cursor,data['transactionId'])
                output_json = json.dumps(output_data)
                self.wfile.write(output_json.encode('utf-8'))
    


    def get_data(self):
        content_length = int(self.headers['Content-Length'])
        #print('content_length:', content_length)
        if content_length:
            input_json = self.rfile.read(content_length)
            input_data = json.loads(input_json)
        else:
            input_data = None
            
        return input_data
