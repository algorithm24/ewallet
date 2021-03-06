from lib2to3.pgen2 import token
from urllib import request, response
from config import TimeoutError
from config import token_required
import config
import uuid
import jwt
import os
import hashlib
import json
import service
import http
import requests

key = os.getenv('SECRET_KEY', 'fortest')

def signup_merchant(connection, cursor,data):
    #query merchant name:
    qry_str = f"""SELECT * 
                FROM public.merchants 
                WHERE name='{data['merchantName']}'
                LIMIT 1
    """
    cursor.execute(qry_str)
    merchant = cursor.fetchone()
    if merchant:
        return {"status":"Merchant Existed"}, 400
    else:
        query = f"""INSERT INTO public.merchants (merchant_url,name)
        VALUES ('{data['merchantUrl']}','{data['merchantName']}')"""
        cursor.execute(query)
        connection.commit()
        qry_str = f"""SELECT * 
                FROM public.merchants 
                WHERE name='{data['merchantName']}'"""
        cursor.execute(qry_str)
        merchant = cursor.fetchone()
        qry = f"""INSERT INTO public.accounts (type,balance,merchant_id)
        VALUES ('merchant',0,'{merchant[0]}') RETURNING account_id"""
        cursor.execute(qry)
        account_id = cursor.fetchone()
        connection.commit()
        response_object = {"merchantName": merchant[2],
                            "accountId":account_id[0],
                            "merchantId": merchant[0],
                            "apiKey": merchant[3],
                            "merchantUrl": merchant[1]
                        }
        config.close_connection(connection,cursor)
        return response_object,200

def new_account(connection, cursor,data):
    if data['accountType'] == 'merchant':
        return {"status":"Can not make merchant account"}, 400
    else:
        id = uuid.uuid4()
        query = f"""INSERT INTO public.accounts (account_id,type,balance)
        VALUES ('{id}','{data['accountType']}',100)"""
        cursor.execute(query)
        connection.commit()
        qry = f"""SELECT * 
                FROM public.accounts
                WHERE account_id='{id}'"""
        cursor.execute(qry)
        account = cursor.fetchone()
        response_object = {"accountType":account[1],
                        "accountId":account[0],
                        "balance":account[2]
        }
        config.close_connection(connection,cursor)
        return response_object,200

@token_required
def topup(token,connection,cursor,data):
    try:
        issuer_account_id = service.decode_token(token)['account_id']
    except:
        return {"code":"wrong type account"},400
    qry = f"""SELECT * FROM public.accounts
    WHERE account_id='{issuer_account_id}'
    AND type='issuer'"""
    cursor.execute(qry)
    account_issuer = cursor.fetchone()
    if not account_issuer:
        config.close_connection(connection,cursor)
        return {"status":"wrong account id or type"},400
    else:
        query = f"""SELECT * FROM public.accounts
        WHERE account_id='{data['accountId']}'
        AND type='personal'"""
        cursor.execute(query)
        account = cursor.fetchone()
        if not account:
            config.close_connection(connection,cursor)
            return {"status":"invalid account"},400
        else:
            qry_str = f"""UPDATE public.accounts
            SET balance=balance+{data['amount']}
            WHERE account_id='{data['accountId']}'"""
            cursor.execute(qry_str)
            connection.commit()
            config.close_connection(connection,cursor)
            return {"status":"success"},200

@config.timeout(300)
@token_required
def transaction_create(token,connection,cursor,data):
    mer_qry = f"""SELECT api_key FROM public.merchants
    WHERE merchant_id='{data['merchantId']}'"""
    cursor.execute(mer_qry)
    merchant_api_key = os.getenv('SECRET_KEY', cursor.fetchone()[0])
    try:
        merchant_account_id = jwt.decode(token,key=merchant_api_key,algorithms='HS256')['account_id']
    except:
        return {"code":"wrong type account"},400
    transaction_id = None
    qry = f"""SELECT * FROM public.accounts
    WHERE account_id='{merchant_account_id}'
    AND type='merchant'"""
    cursor.execute(qry)
    merchant_account = cursor.fetchone()
    if not merchant_account:
        return {"status":"wrong account id or type"},400
    else:
        try:
            signa = {"merchantId":merchant_account[3],
                            "amount":data['amount'],
                            "extraData":data['extraData']
            }
            signature = hashlib.md5(json.dumps(signa).encode('utf-8')).hexdigest()
            query = f"""INSERT INTO public.transactions (merchant_id,account_income_id,amount,extra_data,signature,status)
            VALUES ('{merchant_account[3]}','{merchant_account[0]}',{data['amount']},'{data['extraData']}','{signature}','INITIALIZED') 
            RETURNING transaction_id"""
            cursor.execute(query)
            transaction_id = cursor.fetchone()
            response_object = {"transactionId": transaction_id[0],
                            "merchantId": merchant_account[3],
                            "incomeAccount": merchant_account[0],
                            "outcomeAccount": None,
                            "amount": data['amount'],
                            "extraData": data['extraData'],
                            "signature": signature,
                            "status": "INITIALIZED"
            }
            connection.commit()
            config.close_connection(connection,cursor)
            return response_object,200
        except TimeoutError:
            signa = {"merchantId":merchant_account[3],
                            "amount":data['amount'],
                            "extraData":data['extraData']
            }
            signature = hashlib.md5(json.dumps(signa).encode('utf-8')).hexdigest()
            if not transaction_id:
                query = f"""INSERT INTO public.transactions (merchant_id,account_income_id,amount,extra_data,signature,status)
                VALUES ('{merchant_account[3]}','{merchant_account[0]}',{data['amount']},'{data['extraData']}','{signature}','EXPIRED') 
                RETURNING transaction_id"""
                cursor.execute(query)
                transaction_id = cursor.fetchone()
                response_object = {"transactionId": transaction_id[0],
                            "merchantId": merchant_account[3],
                            "incomeAccount": merchant_account[0],
                            "outcomeAccount": None,
                            "amount": data['amount'],
                            "extraData": data['extraData'],
                            "signature": signature,
                            "status": "EXPIRED"
                }
                connection.commit()
                config.close_connection(connection,cursor)
                return response_object,200
            else:
                query =f"""UPDATE public.transactions
                SET status='EXPIRED'
                WHERE transaction_id='{transaction_id[0]}'"""
                cursor.execute(query)
                response_object = {"transactionId": transaction_id[0],
                            "merchantId": merchant_account[3],
                            "incomeAccount": merchant_account[0],
                            "outcomeAccount": None,
                            "amount": data['amount'],
                            "extraData": data['extraData'],
                            "signature": signature,
                            "status": "EXPIRED"
                }
                connection.commit()
                config.close_connection(connection,cursor)
                return response_object,200

        except:
            signa = {"merchantId":merchant_account[3],
                            "amount":data['amount'],
                            "extraData":data['extraData']
            }
            signature = hashlib.md5(json.dumps(signa).encode('utf-8')).hexdigest()
            query = f"""INSERT INTO public.transactions (merchant_id,account_income_id,amount,extra_data,signature,status)
            VALUES ('{merchant_account[3]}','{merchant_account[0]}',{data['amount']},'{data['extraData']}','{signature}','FAILED') 
            RETURNING transaction_id"""
            cursor.execute(query)
            transaction_id = cursor.fetchone()
            response_object = {"transactionId": transaction_id[0],
                            "merchantId": merchant_account[3],
                            "incomeAccount": merchant_account[0],
                            "outcomeAccount": None,
                            "amount": data['amount'],
                            "extraData": data['extraData'],
                            "signature": signature,
                            "status": "FAILED"
            }
            connection.commit()
            config.close_connection(connection,cursor)
            return response_object,200

@config.timeout(300)
@token_required
def transaction_confirm(token,connection,cursor,transaction_id):
    try:
        personal_account_id = service.decode_token(token)['account_id']
    except:
        return {"code":"wrong type account"},400
    qry = f"""SELECT balance FROM public.accounts
    WHERE account_id='{personal_account_id}'
    AND type='personal'"""
    cursor.execute(qry)
    balance = cursor.fetchone()
    query = f"""SELECT amount,status FROM public.transactions
    WHERE transaction_id='{transaction_id}'"""
    cursor.execute(query)
    data = cursor.fetchone()
    if not data:
        return {"code":"false"},400
    if not balance:
        return {"code":"wrong type account"},400
    if data[1] != 'INITIALIZED':
        return {"code":"wrong status"},400
    if balance[0] >= data[0]:
        qry_str = f"""UPDATE public.transactions
        SET status='CONFIRMED',account_outcome_id='{personal_account_id}'
        WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
        cursor.execute(qry_str)
        # extraData = cursor.fetchone()
        # update(extraData[0],'CONFIRMED')
        connection.commit()
        config.close_connection(connection,cursor)
        return {"code":"confirm successful"},200
    else:
        qry_str = f"""UPDATE public.transactions
        SET status='FAILED',account_outcome_id='{personal_account_id}'
        WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
        cursor.execute(qry_str)
        # extraData = cursor.fetchone()
        # update(extraData[0],'FAILED')
        connection.commit()
        config.close_connection(connection,cursor)
        return {"code":"failed"},400

@config.timeout(300)
@token_required
def transaction_verify(token,connection,cursor,transaction_id):
    try:
        personal_account_id = service.decode_token(token)['account_id']
    except:
        return {"code":"wrong type account"},400
    qry = f"""SELECT status,account_income_id,amount FROM public.transactions
    WHERE transaction_id='{transaction_id}'"""
    cursor.execute(qry)
    data = cursor.fetchone()
    if not data:
        return {"code":"wrong transaction id"},400
    if data[0] != 'CONFIRMED':
        return {"code":"wrong status"},400
    else:
        qry_1 = f"""SELECT balance FROM public.accounts
        WHERE account_id='{personal_account_id}'
        AND type='personal'"""
        cursor.execute(qry_1)
        balance = cursor.fetchone()
        if not balance:
            return {"code":"wrong type account"},400
        query = f"""SELECT amount FROM public.transactions
        WHERE transaction_id='{transaction_id}'"""
        cursor.execute(query)
        amount = cursor.fetchone()
        if not amount:
            return {"code":"false"},400
        if balance[0] >= amount[0]:
            qry_str = f"""UPDATE public.transactions
            SET status='VERIFIED'
            WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
            cursor.execute(qry_str)
            # extraData = cursor.fetchone()
            # update(extraData[0],'VERIFIED')
            connection.commit()
            qry_str = f"""UPDATE public.accounts
            SET balance=balance-{data[2]}
            WHERE account_id='{personal_account_id}'"""
            cursor.execute(qry_str)
            connection.commit()
            qry_str = f"""UPDATE public.accounts
            SET balance=balance+{data[2]}
            WHERE account_id='{data[1]}'"""
            cursor.execute(qry_str)
            connection.commit()
            qry_str = f"""UPDATE public.transactions
            SET status='COMPLETED'
            WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
            cursor.execute(qry_str)
            # extraData = cursor.fetchone()
            # update(extraData[0],'COMPLETED')
            connection.commit()
            config.close_connection(connection,cursor)
            return {"code":"complete successful"},200
        else:
            qry_str = f"""UPDATE public.transactions
            SET status='FAILED'
            WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
            cursor.execute(qry_str)
            # extraData = cursor.fetchone()
            # update(extraData[0],'FAILED')
            connection.commit()
            config.close_connection(connection,cursor)
            return {"code":"false"},400

@config.timeout(300)
@token_required
def transaction_cancel(token,connection,cursor,transaction_id):
    try:
        personal_account_id = service.decode_token(token)['account_id']
        qry_id = f"""SELECT type FROM public.accounts
        WHERE account_id='{personal_account_id}'
        AND type = 'personal'"""
        cursor.execute(qry_id)
        tmp = cursor.fetchone()
        if not tmp:
            return {"code":"wrong type account"},400
    except:
        return {"code":"wrong type account"},400
    qry = f"""SELECT status FROM public.transactions
    WHERE transaction_id='{transaction_id}'"""
    cursor.execute(qry)
    status = cursor.fetchone()
    if not status:
        return {"code":"wrong transaction id"},400
    if status[0] != 'CONFIRMED':
        return {"code":"wrong status"},400
    else:
        qry_str = f"""UPDATE public.transactions
        SET status='CANCELED'
        WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
        cursor.execute(qry_str)
        # extraData = cursor.fetchone()
        # update(extraData[0],'CANCEL')
        connection.commit()
        return {"code":"cancel successful"},200

@token_required
def transaction_expired(token,connection,cursor,transaction_id):
    qry_str = f"""UPDATE public.transactions
    SET status='EXPIRED'
    WHERE transaction_id='{transaction_id}' RETURNING extra_data"""
    cursor.execute(qry_str)
    # extraData = cursor.fetchone()
    # update(extraData[0],'CANCEL')
    connection.commit()
    return {"code":"Expired"},400

def get_token(connection,cursor,data):
    try:
        qry = f"""SELECT merchant_id FROM public.accounts
        WHERE account_id='{data}'"""
        cursor.execute(qry)
        merchant_id = cursor.fetchone()[0]
        if not merchant_id:
            payload = {
                    'account_id': data
                    }
            return jwt.encode(
                        payload,
                        key,
                        algorithm='HS256'
                    ),200
        else:
            qry = f"""SELECT api_key FROM public.merchants
            WHERE merchant_id='{merchant_id}'"""
            cursor.execute(qry)
            merchant_api_key = os.getenv('SECRET_KEY', cursor.fetchone()[0])
            payload = {
                    'account_id': data
                    }
            return jwt.encode(
                        payload,
                        merchant_api_key,
                        algorithm='HS256'
                    ),200
    except Exception as e:
        return e,400

def decode_token(data):
    return jwt.decode(data,key,algorithms='HS256')

def update(extraData,status):
    url = f'http://127.0.0.1:5000/cart/update_status/{extraData}/{status}'
    r = requests.post(url)
    return {"code":"update"},200

