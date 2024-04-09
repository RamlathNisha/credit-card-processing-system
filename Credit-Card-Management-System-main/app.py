from flask import Flask,render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__)
app.secret_key = '830245d3f139432a1b3f9e8dd31a30541fbbcd0b879c6433' 
# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '53052'
app.config['MYSQL_DB'] = 'credit'
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/ext')
def ext():
    return render_template('ext.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/failed')
def failed():
    return render_template('failed.html')

@app.route('/signsubmit', methods = ['POST'])
def signsubmit():
    if request.method == 'POST':
        fname = request.form['fname']
        lname = request.form['lname']
        name = fname + " " + lname
        mail = request.form['mail']
        password = request.form['password']
        connection = mysql.connect
        cur = connection.cursor()
        cur.execute("SELECT COUNT(*) FROM userdetails")
        user_count = cur.fetchone()[0]
        userid = 'usr' + str(user_count + 1).zfill(3)
        # Check if the email already exists
        cur.execute("SELECT COUNT(*) FROM userdetails WHERE mailid = %s", (mail,))
        email_exists = cur.fetchone()[0]
        if email_exists > 0:
            return redirect(url_for('ext'))
        else:
            # Email does not exist, proceed with the insertion
            cur.execute("INSERT INTO userdetails(name,mailid,password,userid) VALUES(%s, %s, %s,%s)", (name, mail, password,userid))
            connection.commit()
            cur.close()
            # Check if the row was successfully inserted
            if cur.rowcount > 0:
                return redirect(url_for('signin'))
            else:
                # Handle the situation where the insertion failed
                return redirect(url_for('signup'))
            
@app.route('/submit', methods = ['POST'])
def submit():
    if request.method == 'POST':
        mail = request.form['mail']
        password = request.form['password']
        connection = mysql.connect
        cur = connection.cursor()
        cur.execute("SELECT mailid,password FROM userdetails WHERE mailid = %s and password = %s", (mail,password))
        user = cur.fetchone()
        cur.close()
        if user:
            additional_data = retrieve_additional_data(mail)
            session['user'] = {'mailid': mail, 'additional_data': additional_data}
            return redirect(url_for('home'))
        else:
            return redirect(url_for('failed'))   
        
def retrieve_additional_data(user_id):
    connection = mysql.connect
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM userdetails WHERE mailid = %s", (user_id,))
    additional_data = cursor.fetchone()
    cursor.close()
    connection.close()
    return additional_data

@app.route('/logout')
def logout():
    return redirect(url_for('signin')) 
    
@app.route('/addcard')
def addcard():
    return render_template('addcard.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/trans')
def trans():
    data = dict(session)
    mail = data['user']['mailid']
    user_data = retrieve_additional_data(mail)
    userid= user_data[3]
    connection = mysql.connect
    cur = connection.cursor()
    cur.execute("SELECT * FROM transactions WHERE userid = %s ORDER BY transaction_id DESC", (userid,))
    transaction_data = cur.fetchall()
    return render_template('trans.html',transactions = transaction_data)

@app.route('/addpro', methods = ['POST'])
def addpro():
    if request.method == "POST":
        num = request.form['credit_card']
        cvv= request.form['cvv']
        npin= request.form['npin']
        edate= request.form['date'] 
        data = dict(session)
        userid= data['user']['additional_data'][3]
        am = 10000
        connection = mysql.connect
        cur = connection.cursor()
        cur.execute("""
    INSERT INTO userdetails (userid, creditcardno, cvv, pinno, expdate, amount)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    creditcardno = VALUES(creditcardno),
    cvv = VALUES(cvv),
    pinno = VALUES(pinno),
    expdate = VALUES(expdate),
    amount = VALUES(amount)
""", (userid, num, cvv, npin, edate, am))
        connection.commit()
        cur.close()
        return redirect(url_for('home'))

@app.route('/addpay', methods = ['POST'])
def addpay():
    if request.method == "POST":
        desc = request.form['desc']
        aspend= request.form['aspend']
        ddate= request.form['pdate']
        pin = request.form['pin']
        data = dict(session)
        mail = data['user']['mailid']
        user_data = retrieve_additional_data(mail)
        userid= user_data[3]
        spin =user_data[6]
        edate= user_data[7]
        tamount = float(user_data[8])
        if pin != spin:
            data = "Invalid PIN"
            return render_template('upcoming.html',data=data)
             # Parse payment date and format as MM/YY
        pdate = datetime.strptime(ddate, '%Y-%m-%d').strftime('%m/%y')
        # Check if payment date doesn't cross expiry date
        if not check_expiry(pdate, edate):
            data = "Credit Card Expired"
            return render_template('upcoming.html',data=data)
        # Check if payment amount exceeds credit card balance
        if float(aspend) > tamount:
            data = "Payment amount exceeds credit card balance"
            return render_template('upcoming.html',data=data)
        connection = mysql.connect
        cur = connection.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions")
        trans_count = cur.fetchone()[0]
        tranid = 'tranid' + str(trans_count + 1).zfill(5)
        cur.close()
        cur1 = connection.cursor()
        cur1.execute("INSERT INTO transactions VALUES(%s, %s,%s,%s,%s)", (tranid,userid,aspend,desc,ddate))
        connection.commit()
        cur1.close()
        aspend= int(aspend)
        new_amount = tamount - aspend
        new_amount = str(new_amount)
        cur2 = connection.cursor()
        cur2.execute("UPDATE userdetails SET amount = %s WHERE userid = %s",(new_amount,userid))
        connection.commit()
        cur2.close()
    # All checks passed, proceed with adding payment to database
    # Add payment to database here
    # Redirect to success page
    return redirect(url_for('success'))


def check_expiry(payment_date, expiry_date):
    payment_month, payment_year = map(int, payment_date.split('/'))
    expiry_month, expiry_year = map(int, expiry_date.split('/'))
    if payment_year < expiry_year or (payment_year == expiry_year and payment_month <= expiry_month):
        return True
    else:
        return False

@app.route('/upcome')
def upcoming_page():
    return render_template('upcoming.html')

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug=True, port=1009)
