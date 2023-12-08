from flask import Flask, render_template, request, redirect, url_for, session, redirect, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import ast
import secrets
import string

app = Flask(__name__, static_folder='static', template_folder='templates')

app.secret_key = 'abce123'


app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'student@256'
app.config['MYSQL_DB'] = 'Movie_booking'

mysql = MySQL(app)

# Character Increment for Seat Booking
def char_filter(s):
    return chr(ord('A') + int(s))

def increment_char_filter(s):
    return chr(ord(s) + 1)

app.jinja_env.filters['char'] = char_filter
app.jinja_env.filters['increment_char'] = increment_char_filter

# Login and First Page
@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer WHERE Username = %s AND password = %s', (username, password, ))
        customer = cursor.fetchone()
        if customer:
            session['loggedin'] = True
            session['custid'] = customer['custid']
            session['name'] = customer['name']
            session['email'] = customer['email']
            message = 'Logged in successfully !'
            return redirect('/home')
        else:
            message = 'Please enter correct email / password !'
    return render_template('login.html',message = message)

# Signup Page
@app.route('/signup', methods =['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'username' in request.form and 'email' in request.form and 'password' in request.form :
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address !'
        elif not username or not password or not email:
            message = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO customer VALUES (NULL, %s, %s, %s, %s)', (name, username, email, password, ))
            mysql.connection.commit()
            message = 'You have successfully registered !'
    elif request.method == 'POST':
        message = 'Please fill out the form !'
    return render_template('signup.html',message = message)

# Logout Page
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# Home Page
@app.route('/home')
def home():
    custid = session.get('custid')
    # print('custid(home):',custid)

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie")
    movies = cur.fetchall()
    cur.close()
    return render_template('home.html', movies = movies,custid=custid)

# Information Page
@app.route('/info/<int:id>/<int:custid>')
def info(id,custid):
    # print('custid(info):',custid)
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie WHERE movieid = %s", (id,))
    movie = cur.fetchone()
    cur.execute("select * from city")
    cities = cur.fetchall()
    cur.close()
    return render_template('information.html', movie=movie, cities=cities, custid=custid)

# Screen and Time Selection
@app.route('/time_select/<int:id>', methods=['GET', 'POST'])
def time_select(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie WHERE movieid = %s", (id,))
    movie = cur.fetchone()

    selected_city = request.args.get('city')
    cur.execute("select * from theatre where theatre.cityId = (select cityId from city where name = %s)", (selected_city,))
    theatre = cur.fetchall()

    screenno = []
    custid = request.args.get('custid')
    # print('custid(time_select):',custid)

    if request.method == 'POST':
        selected_theatre = request.form['value_to_pass']
        var_city = request.form['city_selected']
        
        cur.execute("SELECT st.screenId,st.showtime FROM show_times st INNER JOIN screen s ON st.screenid = s.screenid INNER JOIN theatre t ON s.theatreid = t.theatreid INNER JOIN city c ON t.cityid = c.cityid WHERE t.name = %s AND c.name = %s", (selected_theatre, var_city))
        timming = cur.fetchall()

        cur.execute("SELECT s.screenid,s.screenNo,t.Name FROM Screen s JOIN Theatre t ON s.TheatreId = t.TheatreId JOIN City c ON t.CityId = c.CityId WHERE c.Name = %s and t.Name = %s", (var_city, selected_theatre, ))
        screenno = cur.fetchall()
        return jsonify({'screenno': screenno,'timming':timming})
        
        # print(selected_theatre)
        # for screen in screenno:
        #     print(screen[1])

    cur.close()

    return render_template('time_select.html', movie=movie, theatre=theatre, selected_city=selected_city, screenno=screenno, custid=custid)
    
# Seat Booking 
@app.route('/seat_book/<int:id>', methods=['POST'])
def seat_book(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie WHERE movieid = %s", (id,))
    movie = cur.fetchone()

    cur.execute("update seat set status = 'Booked' where seatId IN (select seatId from booking where Payment_status = 'Yes')")
    mysql.connection.commit()

    cur.execute("select * from seat")
    status = cur.fetchall()
    cur.close()

    custid = request.args.get('custid')
    date = request.form.get('options-base1')
    hall = request.form.get('options-base2')
    screentime = request.form.get('options-base3')
    selected_city = request.args.get('selected_city')

    # print('custid(seat_book):',custid)

    return render_template('seat_book.html',movie=movie,date=date, hall=hall, screentime=screentime, selected_city=selected_city, status=status, custid=custid)

# Payments Page
@app.route('/payment/<int:id>/<int:custid>')
def payment(id,custid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie WHERE movieid = %s", (id,))
    movie = cur.fetchone()
    cur.close()

    # print('custid(payment):',custid)

    return render_template('payment.html', movie=movie, custid=custid)

# Filters Page
@app.route('/filter/<string:str>')
def filter(str):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM movie where language = %s or genre = %s", (str,str))
    movies = cur.fetchall()
    cur.close()
    return render_template('filter.html', movies = movies, filter_str=str)

# Tickets display
@app.route('/ticket/<int:custid>',methods=['GET', 'POST'])
def ticket(custid):
    
    if request.method == 'POST':
        if request.is_json:

            ticket_details = request.get_json()

            movie_name = ticket_details.get('movieName')
            language = ticket_details.get('language')
            city = ticket_details.get('city')
            date = ticket_details.get('date')
            theatre = ticket_details.get('theatre')
            screen_time = ticket_details.get('screenTime')
            tickets = ticket_details.get('tickets')
            selected_seats = ticket_details.get('selectedSeats')
            total = ticket_details.get('total')
            cardholdername = ticket_details.get('cardHolderName')
            bankname = ticket_details.get('bankName')
            cardnumber = ticket_details.get('cardNumber')
            expiry = ticket_details.get('validThrough')
            cvv = ticket_details.get('cvv')
            paymenttype = ticket_details.get('paymentType')

            if paymenttype == 'option1':
                paymenttype = 'Credit Card'
            elif paymenttype == 'option2':
                paymenttype = 'Debit card'
            else:
                paymenttype = 'Gift card'

            # print('cardholdername:',cardholdername)
            # print('bankname:',bankname)
            # print('cardnumber:',cardnumber)
            # print('expiry:',expiry)
            # print('cvv:',cvv)
            # print('Payment Type:',paymenttype)

            alphabet = string.digits + string.ascii_letters
            unique_id = ''.join(secrets.choice(alphabet) for _ in range(12))


            cur = mysql.connection.cursor()
            cur.execute("insert into payment values(NULL,%s,%s,%s,%s)", (custid, total, paymenttype, unique_id, ))
            mysql.connection.commit()
            cur.close()

            cur = mysql.connection.cursor()
            cur.execute("insert into payment_detail values(%s,%s,%s,%s,%s)", (custid, paymenttype, cardholdername, cardnumber, cvv))
            mysql.connection.commit()
            cur.close()

            # Booking Details

            if selected_seats is not None:
                if not isinstance(selected_seats, list):
                    selected_seats = selected_seats.split(', ')
                    print("Selected seats(aa):", selected_seats)
                else:
                    print("Selected seats(aa):", selected_seats)

            match = re.search(r'Screen (\d+) \((.*?)\)', screen_time)

            screen_number = match.group(1)  
            time = match.group(2)  

            cur = mysql.connection.cursor()
            cur.execute("select movieid from movie where title = %s and language = %s", (movie_name,language))
            movieid = cur.fetchone()
            print('movieid:',movieid)
            cur.close()

            cur = mysql.connection.cursor()
            cur.execute("select cityid from city where name = %s", (city, ))
            cityid = cur.fetchone()
            print('cityid:',cityid)
            cur.close()

            cur = mysql.connection.cursor()
            cur.execute("select theatreid from theatre where name = %s and cityId = %s", (theatre,cityid))
            theatreid = cur.fetchone()
            print('theatreid:',theatreid)
            cur.close()

            seatid = []
            
            cur = mysql.connection.cursor()
            for seat in selected_seats:
                cur.execute("select seatid from seat where seatno = %s", (seat, ))
                seats = cur.fetchone()
                seatid.append(seats)
 
            seatid_list = [seat[0] for seat in seatid]
            # print('seatid(bb):', seatid_list)       
            cur.close()
            

            cur = mysql.connection.cursor()
            cur.execute("select screenid from screen where screenno = %s and theatreid = %s", (screen_number,theatreid))
            screenid = cur.fetchone()
            print('screenid:',screenid)
            cur.close()

            cur = mysql.connection.cursor()

            for st in seatid_list:
                cur.execute("insert into booking values(NULL,%s,%s,%s,%s,%s,%s,%s,'Yes',%s)", (custid,movieid,cityid,theatreid,screenid,time,st,date))
                movies = cur.fetchall()
                mysql.connection.commit()
                
            cur.close() 

            cur = mysql.connection.cursor()
            for a in seatid_list:
                cur.execute("update seat set status = 'Booked' where seatid = %s", (a, ))
            mysql.connection.commit()    
            cur.close()

            return jsonify({'message': 'Data received successfully'})
    else:
            return render_template('tickets.html', custid=custid)
    
#Booking Page
@app.route('/booking/<int:custid>')
def booking(custid):
    cur = mysql.connection.cursor()
    cur.execute("SELECT m.title,t.name,s.seatno,sc.screenno,b.time,m.language,c.name,b.date FROM booking b JOIN movie m ON b.movieid = m.movieid JOIN theatre t ON b.theatreid = t.theatreid JOIN city c ON c.cityid = t.cityid JOIN screen sc ON b.screenid = sc.screenid JOIN seat s ON b.seatid = s.seatid WHERE b.custid = %s", (custid, ))
    booking_detail = cur.fetchall()
    # print('movieid:',movieid)
    cur.close()
    return render_template('booking.html',custid=custid,booking_detail=booking_detail)

#Cancel Booking Page
@app.route('/cancel_booking/<int:custid>')
def cancel_booking(custid):

    movie_name = request.args.get('movie_name')
    language = request.args.get('language')

    cur = mysql.connection.cursor()
    cur.execute("select movieid from movie where title=%s and language=%s", (movie_name, language))
    movieid = cur.fetchone()

    # cur = mysql.connection.cursor()
    # cur.execute("select seatid from booking where custid = %s and movieid = %s",(custid, movieid))
    # seatid = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute("delete from booking where  custid = %s and movieid = %s",(custid, movieid))

    cur.close()
    mysql.connection.commit()
    return redirect(url_for('home'))

# main function
if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)