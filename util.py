import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="anpr"
)
cur = mydb.cursor()

def validate_user(username, password):
    # Query the database for the user
    cur.execute("SELECT pass FROM admin WHERE user = %s", (username,))
    result = cur.fetchone()

    # Check if the user exists and the password matches
    if result and result[0]==password:
        return True
    return False

def register_user(username, password):
    try:
        cur.execute("INSERT INTO admin (user, pass) VALUES (%s, %s)", (username,password))
        mydb.commit()
        return "User registered successfully!"
    except Exception as e:
        return f"Error during registration: {e}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}