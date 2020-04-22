from flask import render_template, redirect, session, url_for, request , flash,jsonify
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
    return session.get('user_type') == 'admin'

def is_logged_in():
    return 'user_id' in session and 'user_type' in session

def is_customer():
    return session.get('user_type') == 'customer'

def current_user():
    if 'user_type' in session :
        mycursor = mydb.cursor()
        try:
            mycursor.execute(f"select * from admin where id={session.get('user_id')}") if session.get('user_type') == 'admin' else mycursor.execute(f"select * from customer where id={session.get('user_id')}")
        except:
            print()
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

@app.route('/about')
def about():
    return render_template('about.html')    

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
        hashed_pass = hash_password(password)
        mycursor = mydb.cursor()
        mycursor.execute(f"insert into admin(email,password,shop_name,last_name,first_name,shop_type,Mobile_number) values('{email}','{str(hashed_pass)}','{shop_name}','{lastname_admin}','{firstname_admin}','{shop_type_admin}','{mobile_admin}') ")  
        return redirect(url_for('admin_login'))
    elif request.method == 'GET':
        return render_template('admin_register.html')
    else:
        return redirect(url_for('home'))





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






@app.route('/view_all_customers', methods =['GET','POST'])
def customers():
    if is_logged_in() and is_admin():
        mycursor = mydb.cursor()
        mycursor.execute(f'select * from customer_detail')
        customers = mycursor.fetchall()
        print(customers)
        if len(customers) == 0:
            flash('No customers present currently . Please create customer accounts', 'info')
            return redirect(url_for('customer_register'))
        #print(customers)
        return render_template('view_all_customers.html', customers=customers)

    elif is_customer() and is_logged_in():
        flash('A customer has rights to view his profile only!', 'info')
        return redirect(url_for('customer_home'))
    else :
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
        mycursor.execute(f"Insert into inventory(stock,item_name,item_info,buying_price,selling_price,admin_id,Image_url) values({stock},'{item_name}','{item_info}',{buying_price},{selling_price},{session.get('user_id')},'{imageurl}') ")  
        mydb.commit()
        flash('Inventory added successfully!','success')
        return redirect(url_for('admin_home'))
    if request.method == 'GET' and is_admin():
        print(session)
        return render_template('add_to_inventory.html')
    else:
        flash('Only Admins can add an inventory!', 'info')
        return redirect(url_for('home'))




@app.route('/view_all_inventory/<int:inventory_id>', methods =['GET','POST'])
def update_inventory(inventory_id):
    mycursor = mydb.cursor()
    mycursor.execute(f'select * from inventory where id={inventory_id}') 
    product = mycursor.fetchone()
    old_stock = product['stock']
    #print(type(old_stock))
    #print(product['Image_url'])

    if request.method == 'POST' and is_admin():
        new_stock = request.form['stock']
        new_stock = int(new_stock)
        new_stock += old_stock

        item_name = request.form['item_name']
        item_info = request.form['item_info']
        image_url = str(request.form['image_url'])
        buying_price = request.form['buying_price']
        selling_price = request.form['selling_price']

        mycursor = mydb.cursor()
        mycursor.execute(f"update inventory set stock={new_stock}, item_name='{item_name}', item_info = '{item_info}', Image_url = '{image_url}' , buying_price = {buying_price}, selling_price = {selling_price} where id={inventory_id}")
        mydb.commit()
        flash('Inventory has been updated successfully!','success')
        return redirect(url_for('admin_home'))
    if request.method == 'GET' and is_admin():
        #print(session)
        return render_template('update_inventory.html',inventory_id=inventory_id,product=product)
    else:
        return redirect(url_for('home'))






@app.route('/view_all_inventory', methods = ['GET','POST'])
def view_all_inventory():
    if is_admin():
        mycursor = mydb.cursor()
        mycursor.execute(
            f"select * from inventory where id={session.get('user_id')}")
        inventories = mycursor.fetchall()
        print(inventories)
        if len(inventories)==0:
            flash('No inventory present currently . Please add inventories','info')
            return redirect(url_for('add_to_inventory'))
        return render_template('view_all_inventory.html',inventories=inventories)
    elif is_customer():
        mycursor = mydb.cursor()
        mycursor.execute(
            f"select * from inventory where admin_id = (select admin_id from customer where id = {session.get('user_id')} )")
        inventories = mycursor.fetchall()
        customer =1 
        return render_template('view_all_inventory.html', inventories=inventories,customer = customer)
    else:
        flash('You dont have rights to view!','info')    
        return redirect(url_for('home'))






#customer routes here
@app.route('/customer_register',methods=['GET','POST'])
def customer_register():
    if request.method=='POST' and not is_logged_in():
        print(request.form)
        email_customer=request.form['email']
        password_customer=request.form['password']
        mobile_customer=request.form['mobile']
        address_customer=request.form['address']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        hashed_pass_customer = hash_password(password_customer)
        print(first_name)
        mycursor = mydb.cursor()
        mycursor.execute(f"Insert into customer(email,password) values('{email_customer}','{str(hashed_pass_customer)}') ")
        mycursor.execute(f"select * from customer where email='{email_customer}'")
        customer_id = mycursor.fetchone()['id']
        mycursor.execute(f"Insert into customer_detail(first_name,last_name,mobile_number,address,customer_id) values('{first_name}', '{last_name}','{mobile_customer}','{address_customer}','{customer_id}') ")  
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
        mycursor.execute(f"select * from customer where email='{email}'")
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
    if is_logged_in() and is_customer():
        mycursor = mydb.cursor()
        mycursor.execute(f" select * from customer_detail where customer_id = {session.get('user_id')}")
        customer = mycursor.fetchone()
        return render_template('customer_home.html',customer = customer)
    elif is_logged_in() and is_admin():
        flash('You are not a registered customer!','danger')
        return redirect(url_for('customers'))
    
    else:
        flash('You have not registered!','danger')
        return redirect(url_for('home'))



@app.route('/payments', methods = ['GET','POST'])
def payments():
    if not is_logged_in() and is_customer():
        flash('Please login first!', 'info')
        return redirect(url_for('customer_login'))

    elif is_customer() and request.method == 'POST':
        card_number = request.form['card_number']
        mycursor = mydb.cursor()
        mycursor.execute(
            f"insert into payment(customer_id,card_number) values({session.get('user_id')},{card_number})")
        
        # order and order_items me insert karna hai teko

        flash('Payment done successfully!','success')
        
        return render_template('payments.html')
    else:
        return redirect(url_for('home'))




@app.route('/customer_orders',methods=['GET','POST'])
def customer_orders():
    if not is_logged_in() and is_customer():
        flash('Please login first!','info')
        return redirect(url_for('customer_login'))

    elif is_customer():
        mycursor = mydb.cursor()
        mycursor.execute(f"select * from orders where customer_id = {session.get('user_id')} and admin_id = (select admin_id from customer where id = {session.get('user_id')} )")
        orders = mycursor.fetchall()
        print(orders)
        mycursor.execute(
            f"select * from inventory where id in (select item_id from order_items where order_id in(select id from orders where customer_id = {session.get('user_id')} ))")
        items = mycursor.fetchall()
        print(items)
        return render_template('customer_orders.html', orders = orders,items=items)
    else:
        return redirect(url_for('home'))




@app.route('/shops',methods=['GET','POST'])
def shops():
    if is_logged_in() and is_customer():
        mycursor = mydb.cursor()
        mycursor.execute(f" select * from admin ")
        admin_shops  = mycursor.fetchall()
        return render_template("shops.html",admin_shops = admin_shops)
    elif is_logged_in() and is_admin():
        return redirect(url_for('admin_home'))
    else:
        return redirect(url_for('home'))




@app.route('/shops/<int:admin_id>', methods=['GET','POST'])
def view_shop(admin_id):
    if is_customer() and is_logged_in():
        mycursor = mydb.cursor()
        mycursor.execute(f"select * from inventory where admin_id = {admin_id}")
        admin_inventories = mycursor.fetchall()
        
        print(admin_inventories)

        mycursor = mydb.cursor()
        mycursor.execute(f"select * from admin where id = {admin_id}")
        admin = mycursor.fetchone()
        return render_template('view_shop.html',admin_inventories=admin_inventories,admin=admin)
    elif is_customer():
        flash('Please login first!','info')
        return redirect(url_for('customer_login'))
    else:
        return redirect(url_for('home'))


#ek baar admin banke add , view , update check jaro inventory
# id pe click karna for updste    
#cart related routes

@app.route('/add_to_cart',methods=['POST'])
def add_to_cart():
    if request.method == 'POST' and is_customer():
        product_id = str(request.json['product_id'])
        if not session.get('cart'):
            session['cart'] = {}
        if product_id not in session['cart']:
            session['cart'][product_id] = 0
        session['cart'][product_id] += 1
        print(session['cart'][product_id])
        session.modified = True
        print(product_id)
        return jsonify({'added':True})
    return jsonify({'added':False})


@app.route('/decrease_from_cart',methods=['POST'])
def decrease_from_cart():
    if request.method == 'POST' and is_customer():
        product_id = str(request.json['product_id'])
        if session['cart']:
            if product_id in session['cart']:
                session['cart'][product_id] -= 1
                if session['cart'][product_id] == 0:
                    session['cart'].pop(product_id)
                session.modified = True
                is_cart_empty()
                return jsonify({'decreased':True,'invalid':False})
            else:
                return jsonify({'decreased':False,'invalid':False})
        else:
            return jsonify({'decreased':False,'invalid':True})
    else:
        return jsonify({'decreased':False,'invalid':True})



@app.route('/remove_from_cart',methods=['GET','POST'])
def remove_from_cart():
    if request.method == 'POST' and is_customer():
        product_id = str(request.json['product_id'])
        if product_id in session['cart']:
            session['cart'].pop(product_id)
            is_cart_empty()
            session.modified = True
            return jsonify({'removed':True,'invalid':False})
        else:
            return jsonify({'removed':False,'invalid':False})
    return jsonify({'removed':False,'invalid':True})



@app.route('/view_cart',methods=['GET'])
def view_cart():
    if is_customer():
        items = None
        if 'cart' in session:
            items = (x for x in session['cart'])
            mycursor = mydb.cursor()
            st = "select * from inventory where id in ("
            st += ", ".join(items)
            st += ");"
            print(st)
            mycursor.execute(st)
            result = mycursor.fetchall()
            print(result)
            items = [(x,session['cart'][str(x['id'])]) for x in result]
        else:
            flash('Cart is empty. Please add items','info')
            return redirect(url_for('customer_home'))    
        return render_template('view_cart.html',items = items)
    else:
        return redirect(url_for('home'))


@app.route('/checkout',methods=['GET','POST'])
def checkout():
    if is_customer():
        items = None
        if 'cart' in session:
            items = (x for x in session['cart'])
            mycursor = mydb.cursor()
            st = "select * from inventory where id in ("
            st += ", ".join(items)
            st += ");"
            print(st)
            mycursor.execute(st)
            result = mycursor.fetchall()
            print(result)
            items = [(x,session['cart'][str(x['id'])]) for x in result]
            admin_id = result[0]["admin_id"]

            # yaha pe bas 2 queries likde order and order_items ka 
            # first take only the card_number from form then insert into payment
            # payment ka route me sab code hai
            # then 2 inserts and then orders wala html page banao ..

            #items is the list of tupple with the product at first index and its quantity at second index
            #iske aage registering ka code likh do tum and vo view_cart vala ui hag raha hai because of mdb template
            
            
            if request.method=="POST" and is_logged_in():
                card_number = request.form['card_number']
                mycursor = mydb.cursor()
                mycursor.execute(f"insert into payment(customer_id,card_number)values('{session.get('user_id')}','{card_number}')")
                mydb.commit()
                mycursor.execute('SELECT last_insert_id()')
                payment_id = mycursor.fetchone()
                # print(payment_id)
                # print(payment_id['last_insert_id()'])
                
                
                
                mycursor.execute(f"insert into orders(customer_id,admin_id,payment,payment_id)values('{session.get('user_id')}','{admin_id}','{1}','{payment_id['last_insert_id()']}')")
                mycursor.execute('SELECT last_insert_id()')
                order_id = mycursor.fetchone()
                mydb.commit()


                for i in items:
                    # print("i is :" ,i)
                    # print("0 is :",i[0])
                    # print(i[1])
                    mycursor.execute(f"insert into order_items(item_id,order_id,quantity)values('{i[0]['id']}','{order_id['last_insert_id()']}','{i[1]}')")
                    mydb.commit()
                flash("Checked out successfully","success")
                return redirect(url_for('customer_home')) 
                
            elif not is_logged_in():
                return redirect(url_for('home'))
            
            return render_template('checkout.html',items = items)
                



            
    
        




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




    
