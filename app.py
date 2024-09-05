from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import folium

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for sessions

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('disaster_reports.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('register.html')

# Example login function
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('disaster_reports.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        return redirect(url_for('home'))
    return 'Invalid login credentials'

# Report a Disaster Route
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        user_id = request.form['user_id']
        location = request.form['location']
        disaster_type = request.form['disaster_type']
        description = request.form['description']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        conn = sqlite3.connect('disaster_reports.db')
        c = conn.cursor()
        c.execute('''INSERT INTO reports (user_id, location, disaster_type, description, latitude, longitude)
                     VALUES (?, ?, ?, ?, ?, ?)''', (user_id, location, disaster_type, description, latitude, longitude))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('report.html')

# Admin Dashboard Route
@app.route('/admin')
def admin():
    conn = sqlite3.connect('disaster_reports.db')
    c = conn.cursor()
    c.execute('''SELECT reports.id, users.username, reports.location, reports.disaster_type, 
                        reports.description, reports.latitude, reports.longitude
                 FROM reports
                 JOIN users ON reports.user_id = users.id''')
    reports = c.fetchall()
    conn.close()

    # Create a map with reported disasters
    report_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
    for report in reports:
        if report[5] and report[6]:  # Ensure latitude and longitude are valid
            popup_text = f"Reported by {report[1]}: {report[3]} - {report[4]}"
            folium.Marker([report[5], report[6]], popup=popup_text).add_to(report_map)
    
    report_map.save('static/map.html')
    return render_template('admin.html', reports=reports)

# Messaging route for communication between disaster reporters and responders
@app.route('/messages/<int:receiver_id>', methods=['GET', 'POST'])
def messages(receiver_id):
    if request.method == 'POST':
        sender_id = request.form['sender_id']
        message = request.form['message']
        conn = sqlite3.connect('disaster_reports.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
                  (sender_id, receiver_id, message))
        conn.commit()
        conn.close()
        return redirect(url_for('messages', receiver_id=receiver_id))
    
    conn = sqlite3.connect('disaster_reports.db')
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)",
              (session['user_id'], receiver_id, receiver_id, session['user_id']))
    messages = c.fetchall()
    conn.close()
    
    return render_template('messages.html', messages=messages, receiver_id=receiver_id)

if __name__ == '__main__':
    app.run(debug=True)
