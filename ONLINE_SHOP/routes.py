from flask import render_template, redirect, session, url_for, request , flash
import pymysql
from datetime import date, datetime
import smtplib
from flask_mail import Mail, Message
from passlib.hash import sha256_crypt
from ONLINE_SHOP import app , mydb , mail

#all the side functions here

def hash_password(password):
    return sha256_crypt.encrypt(password)

def compare_password(password, expected):
    return sha256_crypt.verify(password,expected)

def is_admin():
    return session['user_type'] == 'admin'

def is_logged_in():
    return 'user_id' in session and 'user_type' in session

def is_customer():
    return session['user_type'] == 'customer'

def current_user():
    if 'user_type' in session :
        mycursor = mydb.cursor()
        mycursor.execute(f"select * from admin where id={session['user_id']}") if session['user_type'] == 'admin' else mycursor.execute(f"select * from customer where id={session['user_id']}")
        myresult = mycursor.fetchone()
        return myresult
    else:
        return None

def is_cart_empty():
    if len(session['cart'])==0:
        session.pop('cart')

count = 0

#basic home route

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route("/tables")
def tables():
    return render_template('tables.html')

#admin routes here

@app.route('/admin_register',methods=['GET','POST'])
def admin_register():
    if request.method=='POST' and not is_logged_in():
        firstname_admin = request.form['firstname']
        lastname_admin = request.form['lastname']
        shop_type_admin = request.form['shop_type']
        mobile_admin = request.form['mobile']
        email=request.form['email']
        shop_name = request.form['shop_name']   
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        # if password != confirm_password:kya hua? comment kyu?
        #     flash('Confirm password not matching the Password!','danger')
        #     return redirect(url_for('admin_register'))
        hashed_pass = hash_password(password)
        mycursor = mydb.cursor()
        mycursor.execute(f"insert into admin(email,password,shop_name,last_name,first_name,shop_type,Mobile_number) values('{email}','{str(hashed_pass)}','{shop_name}','{lastname_admin}','{firstname_admin}','{shop_type_admin}','{mobile_admin}') ")  
        mydb.commit()
        flash("Admin account created successfully","success")
        return redirect(url_for('admin_login'))
    #elif request.method == 'GET' and not is_logged_in():
    return render_template('admin_register.html')   
 #   else:
  #      return redirect(url_for('home'))



@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method == 'POST' and not is_logged_in():
        email = request.form['email']
        password = request.form['password']
        mycursor = mydb.cursor()
        mycursor.execute(f"select * from admin where email='{email}'")
        expected = mycursor.fetchone()
        if compare_password(password, expected['password']):
            session['user_type'] = 'admin'
            session['user_id'] = expected['id']
            return redirect(url_for('admin_home'))
        else:
            return render_template('admin_login.html')
    elif request.method == 'GET':
        return render_template('admin_login.html')
    else:
        return redirect(url_for('home'))





@app.route('/admin_home',methods=['GET'])
def admin_home():
    if is_admin():
        return render_template('dashboard.html')
    else:
        return redirect(url_for('home'))



# Inventory routes here    

@app.route('/add_to_inventory', methods = ['GET','POST'])
def add_to_inventory():
    if request.method == 'POST' and is_admin() :
        print(session)
        stock = request.form['stock']
        item_name = request.form['item_name']
        item_info = request.form['item_info']
        imageurl = str(request.form['image_url'])
        buying_price = request.form['buying_price']
        selling_price = request.form['selling_price']
        mycursor = mydb.cursor()
        mycursor.execute(f"Insert into inventory(stock,item_name,item_info,buying_price,selling_price,admin_id,Image_url) values({stock},'{item_name}','{item_info}',{buying_price},{selling_price},{session['user_id']},'{imageurl}') ")  
        mydb.commit()
        return redirect(url_for('admin_home'))
    if request.method == 'GET' and is_admin():
        print(session)
        return render_template('add_to_inventory.html')
    else:
        return redirect(url_for('home'))


@app.route('/update_inventory/<int:inventory_id>', methods =['GET','POST'])
def update_inventory(inventory_id):
    mycursor = mydb.cursor()
    mycursor.execute(f'select * from inventory where id={inventory_id}') 
    product = mycursor.fetchone()
    old_stock = product['stock']

    if request.method == 'POST':
        new_stock = request.form['stock']
        new_stock += old_stock
        mycursor = mydb.cursor()
        mycursor.execute(f'update inventory set stock={new_stock} where id={inventory_id}')
        mydb.commit()

    if request.method == 'GET':
            ...



@app.route('/view_all_inventory', methods = ['GET','POST'])
def view_all_inventory():
    mycursor = mydb.cursor()
    mycursor.execute(f'select * from inventory') 
    inventories = mycursor.fetchall()
    if len(inventories)==0:
        flash('No inventory present currently . Please add inventories','info')
        return redirect(url_for('add_to_inventory'))
    return render_template('view_all_inventory.html',inventories=inventories)





#customer routes here
@app.route('/customer_register',methods=['GET','POST'])
def customer_register():
    if request.method=='POST' and not is_logged_in():
        email_customer=request.form['email']
        password_customer=request.form['password']
        mobile_customer=request.form['mobile']
        address_customer=request.form['address']
        # confirm_password = request.form['confirm_password']
        # if password != confirm_password:
        #     flash('Confirm password not matching the Password!','danger')
        #     return redirect(url_for('customer_register'))
        #implement this in frontend

        hashed_pass_customer = hash_password(password_customer)

        mycursor = mydb.cursor()
        mycursor.execute(f"Insert into customer(email,password) values('{email_customer}','{str(hashed_pass_customer)}') ")  
        customer_id=mydb.session['id']
        mycursor.execute(f"Insert into customer_details(mobile_number,address,customer_id) values('{mobile_customer}','{address_customer}',{customer_id}) ")  
        mydb.commit()
        return redirect(url_for('customer_login'))
    elif request.method == 'GET':
        return render_template('customer_register.html')
    else:
        return redirect(url_for('home'))


@app.route('/customer_login',methods=['GET','POST'])
def customer_login():
    if request.method == 'POST' and not is_logged_in():
        email = request.form['email']
        password = request.form['password']
        mycursor = mydb.cursor()
        mycursor.execute(f"select * from customer where email={email}")
        expected = mycursor.fetchone()
        if compare_password(password, expected['password']):
            session['user_type'] = 'customer'
            session['user_id'] = expected['id']
            return redirect(url_for('customer_home'))
        else:
            return render_template('customer_login.html')
    elif request.method == 'GET':
        return render_template('customer_login.html')
    else:
        return redirect(url_for('home'))

@app.route('/customer_home',methods=['GET'])
def customer_home():
    if is_customer():
        return render_template('dashboard.html')
        
#cart related routes

@app.route('/decrease_from_cart',methods=['POST'])
def decrease_from_cart():
    if request.method == 'POST' and is_customer():
        product_id = request.get_json()['product_id']
        if session['cart']:
            if product_id in session['cart']:
                session['cart'][product_id] -= 1
                if session['cart'][product_id] == 0:
                    session['cart'].pop(product_id)
                session.modified = True
                is_cart_empty()
                return {'decreased':True,'invalid':False}
            else:
                return {'decreased':False,'invalid':False}
        else:
            return {'decreased':False,'invalid':True}
    else:
        return {'decreased':False,'invalid':True}


@app.route('/remove_from_cart',methods=['GET','POST'])
def remove_from_cart():
    if request.method == 'POST' and is_customer():
        product_id = request.get_json()['product_id']
        if product_id in session['cart']:
            session['cart'].pop(product_id)
            is_cart_empty()
            session.modified = True
            return {'removed':True,'invalid':False}
        else:
            return {'removed':False,'invalid':False}
    return {'removed':False,'invalid':True}

@app.route('/view_cart',methods=['GET'])
def view_cart():
    if is_customer():
        if session['cart']:
            items = (x for x in session['cart'])
            mycursor = mydb.cursor()
            mycursor.execute(f"select * from inventory where id in {items}")
            result = mycursor.fetchall()
            items = [(x,session['cart'][x['id']]) for x in result]
        return render_template('view_cart.html',items = items)
    else:
        return redirect(url_for('home'))

#Logout
@app.route('/logout',methods=['GET','POST'])
def logout():
    if is_logged_in():
        session.pop('user_id')
        session.pop('user_type')
        modified = True
    print(session)
    return redirect(url_for('home'))

#bottom
@app.context_processor
def currentuser():
    return dict(current_user=current_user())




    