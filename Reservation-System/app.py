from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3
from itertools import chain, zip_longest

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret'

DATABASE = 'reservations.db'

def get_cost_matrix():
    cost_matrix = [[100, 75, 50, 100] for row in range(12)]
    return cost_matrix

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/reservation')
def reservation():
    seat_matrix = [['O' for _ in range(4)] for _ in range(12)]  #Create a 12x4 matrix of 'O'

    for row, col in get_seats():
        seat_matrix[row][col] = 'X'

    return render_template('reservation.html', seat_matrix=seat_matrix)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        cur = db.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        result = cur.fetchone()
        if result:
            return redirect(url_for('admin'))
        else:
            error_message = "Incorrect username or password. Please try again."
            return render_template('login.html', error=error_message)
    else:
        return render_template('login.html')

@app.route('/admin')
def admin():
    seat_matrix = [['O' for _ in range(4)] for _ in range(12)]  #Create a 12x4 matrix of 'O'

    #Update the matrix with 'X' where seats are reserved
    for row, col in get_seats():
        seat_matrix[row][col] = 'X'
    
    total_sales = sum(get_cost_matrix()[row][col] if seat == 'X' else 0 
                      for row, line in enumerate(seat_matrix) 
                      for col, seat in enumerate(line))

    return render_template('admin.html', seat_matrix=seat_matrix, total_sales=total_sales)

def get_seats():
    db = get_db()
    cur = db.execute("SELECT seatRow, seatColumn FROM reservations")
    return cur.fetchall()

@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    for value in request.form.values():
        if not value:
            flash("Please fill out all fields.")
            return reservation()
    
    row = int(request.form.get('row_select')) - 1
    column = int(request.form.get('seat_select')) - 1

    if not check_seat_reservation(row, column):
        flash("Seat is already booked. Please choose a valid seat.")
        return reservation()
    
    print(request.form.get('row_select'))

    db = get_db()

    query = '''INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber, created) 
               VALUES (?, ?, ?, ?, (SELECT strftime(\'%Y-%m-%d %H:%M:%S\', datetime(\'now\'))))'''
    userInfo = (
        request.form.get('first_name'),
        row,
        column,
        ''.join(chain(*zip_longest(request.form.get('first_name'), 'INFOTC4320', fillvalue='')))
    )

    db.execute(query, userInfo)
    db.commit()

    e_ticket_number = ''.join(chain(*zip_longest(request.form.get('first_name'), 'INFOTC4320', fillvalue='')))  # Generate e-ticket number

    flash(f"Your booking is confirmed.\n E-ticket number: {e_ticket_number}", "success")

    return reservation()


def check_seat_reservation(row, col):
    db = get_db()

    query = 'SELECT * FROM reservations WHERE seatRow = ? AND seatColumn = ?'
    cur = db.execute(query, (row, col))

    result = cur.fetchone()

    if result:
        return False
    return True

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
