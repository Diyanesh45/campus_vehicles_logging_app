import atexit, shutil, os
import mysql.connector
from flask import Flask, render_template, request, flash, redirect, url_for, session, make_response, send_file
from flask_session import Session
from functools import wraps

# Setup the MySQL connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="anpr"
)
cur = mydb.cursor()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session and flash

app.config['SESSION_TYPE'] = 'filesystem'  # Store sessions on the server's filesystem
app.config['SESSION_PERMANENT'] = False  # Make sessions non-permanent
app.config['SESSION_FILE_DIR'] = './sessions'  # Directory to store session files
Session(app)

UPLOAD_FOLDER = os.path.join('static', 'uploads')  # Store files in 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("You must log in to access this page.", "error")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def login_page():
    if 'username' in session:
        return redirect(url_for('home_page'))
    response = make_response(render_template("login.html"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        from util import validate_user
        
        if validate_user(username, password):  # Validate user credentials
            session['username'] = username
            return redirect(url_for("home_page"))
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for("login_page"))
    
    return render_template("login.html")

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        retype_password = request.form.get("retype_password")

        # Check if passwords match
        if password != retype_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for("signup"))

        # Check if the username already exists
        try:
            cur.execute("SELECT * FROM admin WHERE user = %s", (username,))
            existing_user = cur.fetchone()
            if existing_user:
                flash("Username already exists. Please choose another one.", "error")
                return redirect(url_for("signup"))
        except Exception as e:
            flash(f"Database error: {e}", "error")
            return redirect(url_for("signup"))

        # Register the new user
        from util import register_user
        msg = register_user(username, password)
        flash(msg, "success")
        return redirect(url_for("login_page"))
    
    return render_template("signup.html")

@app.route('/home', methods=["GET", "POST"])
def home_page():
    # Redirect to login if the user is not logged in
    if 'username' not in session:
        flash("Please log in First.", "error")
        return redirect(url_for('login_page'))
    
    # Path to the vehicle data CSV
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline', 'vehicle_data.csv')

    # Load the vehicle data from the CSV file if it exists
    vehicle_data = []
    if os.path.exists(csv_file_path):
        import pandas as pd
        vehicle_data = pd.read_csv(csv_file_path).to_dict(orient='records')

    response = make_response(render_template("home.html", username=session['username'], vehicle_data=vehicle_data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
@app.route('/upload_files', methods=['POST', 'GET'])
def upload_files():
    from util import allowed_file

    # Check if either 'in_video' or 'out_video' is present in the request
    in_video_file = request.files.get('in_video')
    out_video_file = request.files.get('out_video')

    # Ensure at least one file is uploaded
    if not in_video_file and not out_video_file:
        flash("No file uploaded", "error")
        return redirect(url_for('home_page'))

    # Define the upload folder and video paths
    upload_folder = app.config['UPLOAD_FOLDER']
    in_video_path = os.path.join(upload_folder, 'in_video.mp4')
    out_video_path = os.path.join(upload_folder, 'out_video.mp4')

    # Delete any existing video (either 'in' or 'out') to ensure only one exists at a time
    if os.path.exists(in_video_path):
        os.remove(in_video_path)
    if os.path.exists(out_video_path):
        os.remove(out_video_path)

    # Handle the "in" video upload if present
    if in_video_file and allowed_file(in_video_file.filename):
        os.makedirs(upload_folder, exist_ok=True)  # Create directory if not exists
        in_video_file.save(in_video_path)
        flash("Vehicle In video uploaded successfully", "success")

    # Handle the "out" video upload if present
    elif out_video_file and allowed_file(out_video_file.filename):
        os.makedirs(upload_folder, exist_ok=True)  # Create directory if not exists
        out_video_file.save(out_video_path)
        flash("Vehicle Out video uploaded successfully", "success")

    # Redirect back to the home page
    return redirect(url_for('home_page'))


@app.route('/play_video/<video_type>', methods=["GET"])
def play_video(video_type):
    # Determine the file path and URL based on the video type
    if video_type == 'in':
        video_path = 'static/uploads/in_video.mp4'  # Use forward slashes
    elif video_type == 'out':
        video_path = 'static/uploads/out_video.mp4'
    else:
        flash('Invalid video type!')
        return redirect(url_for('home_page'))
    
    # Check if the file exists
    full_path = os.path.join(app.root_path, video_path)
    if not os.path.exists(full_path):
        flash('No file found for the selected video!')
        return redirect(url_for('home_page'))
    # Render the template with the video path
    return render_template('play_video.html', video_path=url_for('static', filename=f'uploads/{os.path.basename(video_path)}'))

from flask import Flask, request, jsonify
import subprocess

@app.route('/start-detection', methods=['POST'])
def start_detection():
    import os
    import subprocess
    from flask import request, jsonify
    import pandas as pd
    from datetime import datetime

    video_type = request.json.get('video_type', 'in')  # 'in' or 'out'

    # Resolve paths
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    video_path = os.path.join(current_dir, 'static', 'uploads', f"{video_type}_video.mp4")
    main_script_path = os.path.join(current_dir, 'pipeline', 'main.py')
    csv_file_path = os.path.join(current_dir, 'pipeline', 'vehicle_data.csv')  # Data file

    if not os.path.exists(video_path):
        return jsonify({'error': f"Video file not found: {video_path}"}), 404

    try:
        # Trigger the main.py script with the video path
        subprocess.run(['python', main_script_path, video_path], check=True)

        # Load the result file with detected license numbers and timestamps
        detection_result_path = os.path.join(current_dir, 'pipeline', 'license_and_timestamp.csv')
        detection_data = pd.read_csv(detection_result_path)

        # Load or create the vehicle data table
        if os.path.exists(csv_file_path):
            vehicle_data = pd.read_csv(csv_file_path)
        else:
            vehicle_data = pd.DataFrame(columns=['license_number', 'in_time', 'out_time'])

        # Update the table
        for _, row in detection_data.iterrows():
            license_number = row['license_number']
            timestamp = row['timestamp']

            if video_type == 'in':
                # Add a new entry if 'in' type video is processed
                if license_number not in vehicle_data['license_number'].values:
                    vehicle_data = pd.concat([
                        vehicle_data,
                        pd.DataFrame({'license_number': [license_number], 'in_time': [timestamp], 'out_time': [None]})
                    ], ignore_index=True)
            elif video_type == 'out':
                # Update the 'out_time' if 'out' type video is processed
                vehicle_data.loc[
                    (vehicle_data['license_number'] == license_number) & (vehicle_data['out_time'].isnull()),
                    'out_time'
                ] = timestamp

        # Save the updated table
        vehicle_data.to_csv(csv_file_path, index=False)

        return jsonify({'message': 'Detection and table update completed successfully!'}), 200

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f"Failed to start detection: {str(e)}"}), 500


@app.route('/vehicle-data', methods=['GET','POST'])
def vehicle_data():
    import os
    import pandas as pd

    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline', 'vehicle_data.csv')

    if os.path.exists(csv_file_path):
        vehicle_data = pd.read_csv(csv_file_path)
        return vehicle_data.to_dict(orient='records')
    else:
        return []

@app.route("/logout")
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out successfully.", "success")
    return redirect("/")

def cleanup_sessions():
    """Clear the session data when the server shuts down."""
    print("Cleaning up session files...")
    session_file_dir = app.config['SESSION_FILE_DIR']
    if os.path.exists(session_file_dir):
        shutil.rmtree(session_file_dir)  # Remove the session directory and its contents
    session_file_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(session_file_dir):
        shutil.rmtree(session_file_dir)  # Remove the session directory and its contents
    file_paths=[r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\__pycache__',r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\pipeline\__pycache__',r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\pipeline\license_and_timestamp.csv',r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\pipeline\test_interpolated.csv',r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\pipeline\test.csv',r'C:\Users\ASUS\OneDrive\Desktop\S7\anpr\pipeline\vehicle_data.csv']
    for path in file_paths:
        if os.path.exists(path) and path[len(path)-4:]=='.csv':    
            os.remove(path)
        elif os.path.exists(path):
            shutil.rmtree(path)    
    
atexit.register(cleanup_sessions)

if __name__ == '__main__':
    app.run(debug=True)
