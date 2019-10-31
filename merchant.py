from flask import Flask, render_template, request, redirect, jsonify
import os
import random
import requests
from urllib.parse import urlencode
import mysql.connector
from subprocess import check_output
import json

app=Flask(__name__)
# print(app.jinja_env.autoescape)
port = int(os.getenv("PORT", 8000))

global ip_addr
global merchant_port
global bank_port
global pg_port

def create_json(merchant_port=8000, pg_port=5000, bank_port=5001):
    ip_addr = (str(check_output(['hostname', '-I'])).split(" ")[0])[2:]
    print(ip_addr)
    with open("config.conf", "w") as config:
        conf = {'ip_addr': ip_addr, 
                'merchant_port': merchant_port,
                'pg_port': pg_port,
                'bank_port': bank_port 
               }
        json.dump(conf, config)

def read_conf(filename):
    with open(filename) as config:
        conf = json.load(config)
        return conf

def generate_orderid():
	return random.randint(1000000000000, 9999999999999)

def gen_url(base_url, params):
	qstr = urlencode(params)
	return base_url + "?" + qstr

def get_columns_db(connection, table_name):
    cursor = connection.cursor()
    cursor.execute("desc {}".format(table_name))
    return [column[0] for column in cursor.fetchall()]

def total_amount(products_list:list):
    totalAmount = 0
    for product in products_list:
        totalAmount += product['quantity']* int(product['unit_price'])

    return totalAmount

def read_db(connection, table_name, column_names:dict=None):
    cursor = connection.cursor()
    search_str = "*"
    if column_names is not None:
        search_str = ""
        for column_name in column_names:
            search_str += column_name + "=" + "'" + column_names[column_name] + "', "
        search_str = search_str[:-2]
    try:  
        #Reading the Employee data      
        cursor.execute("SELECT * from {} WHERE {}".format(table_name, search_str))  
      
        #fetching the rows from the cursor object  
        result = cursor.fetchall() 
        print(result) 
        return result 
    except Exception as e: 
        print(e) 
        connection.rollback()  
    connection.close()  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cart')
def cart():
	order_id = generate_orderid()
	return render_template('cart1.html', order_id=order_id, merchant_id=merchant_id)

@app.route('/new_payment', methods=['POST'])
def new_payment():
	# Take more user info
    order = request.form.to_dict()

    api_url = payment_gateway_redirect['card']
    url_ = {'order_id': order['order_id'], 'merchant_id': order['merchant_id']}
    post_url = gen_url(api_url, url_)

    print(post_url)
    
    # Merchant's database Columns
    # cart_id, email, phone, first_name, last_name
    # columns = ['cart_id', 'email', 'phone', 'first_name', 'last_name']
    columns = get_columns_db(merchant_db, 'user_info')
    buyer = {}

    result = read_db(merchant_db, 'user_info', {'email':login_user_email})

    for row in result:
        for column_no in range(len(row)):
            buyer[columns[column_no]] = row[column_no]

    columns = get_columns_db(merchant_db, 'cart_info')
    result = read_db(merchant_db, 'cart_info', {'cart_id': buyer['cart_id']})
    products = []

    for row in result:
        product = {}
        for column_no in range(len(row)):
            if columns[column_no] != 'cart_id':
                product[columns[column_no]] = row[column_no]
        products.append(product)

    order["buyer"] = buyer
    order["products"] = products
    order["total_amount"] = total_amount(products)

    # order["PaymentMethod"] = 'CARD'
    order["return_URL"] = {"positive_URL": 'http://{}:{}/payment_success'.format(ip_addr, merchant_port),
                            "negative_URL": 'http://{}:{}/payment_failed'.format(ip_addr, merchant_port)}

    print(order) 

    r = requests.post(url=post_url, json=order)
    print(r.json())
    return redirect(post_url)

@app.route('/payment_success', methods=['GET', 'POST'])
def success():
	params = request.args.to_dict()
	print(params)
	# return jsonify(params)
	return render_template('success.html', params=params)

@app.route('/payment_failed', methods=['GET', 'POST'])
def failure():
	params = request.args.to_dict()
	print(params)
	# return jsonify(params)
	return render_template('failure.html', params=params)


if __name__ == '__main__':
    create_json()

    conf = read_conf('config.conf')
    ip_addr = conf['ip_addr']
    merchant_port = conf['merchant_port']
    bank_port = conf['bank_port']
    pg_port = conf['pg_port']

    merchant_id = "qwertyuiop"
    payment_gateway_redirect = {'card': 'http://{}:{}/redirect'.format(ip_addr, pg_port)}

    # Assumption
    # John Doe is logged in. The login details will be taken from the session user

    login_user_email = "john@gmail.com"

    merchant_db = mysql.connector.connect(host = "127.0.0.1", user = "root",passwd = "123456789", database = "merchant_db")  


    app.run(host = '0.0.0.0', port = port, debug=True)
