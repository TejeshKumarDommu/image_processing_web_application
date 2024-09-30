from flask import Flask, g, session, render_template, request, redirect, url_for, flash
import mysql.connector 
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
import torch
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'sdjbgfkjsnkjsdbfiu'

app.config['UPLOAD_FOLDER'] = "static\\uploads"
app.config['PROCESS_FOLDER'] = "static\\processed_images"
app.config['SECRET_KEY']  = "teja@212000"

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "Teja@212000@dommu"
app.config['MYSQL_DB'] = "deepcorn"


def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'])
        g.cursor = g.db.cursor(dictionary=True)
    return g.db, g.cursor

def close_db(e=None):
    db=g.pop('db', None)
    if db is not None:
        db.close()
        
# @app.teardown_appcontext
# def teardown_db(e=None):
#     close_db(e)
        
def length_width(image):
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.threshold(blur, 0, 150, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    
    # Find bounding box
    x,y,w,h = cv2.boundingRect(thresh)
    cv2.rectangle(image, (x, y), (x + w, y + h), (36,255,12), 2)
    
    length = w
    width = h
    dpi = 72
    width_cm = round((width / dpi * 1.90)/3)
    length_cm = round((length / dpi * 1.90)/3)
    
    
    

    #cv2.putText(image, "h={}cm,w={}cm".format(width_cm,length_cm), (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (36,255,12), 1)

    # Print the length and width of the object
    #print(f"Width of Corn : {length_cm} cm")
    #print(f"Length of Corn : {width_cm} cm")
    
    return width_cm, length_cm, gray


def kernel_count(image):
    
# Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Apply adaptive thresholding to segment the image
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 111, 4)


    thresh_1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 5)

# Find contours in the thresholded image
    contours, _ = cv2.findContours(thresh_1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Initialize a counter to keep track of the number of kernels
    kernel_count = 0

# Iterate over the contours and count the kernels
    for contour in contours:
    # Calculate the area of the contour
        area = cv2.contourArea(contour)
    
    # If the area is within a certain range, consider it as a kernel
        if area > 150 and area < 1000:
            kernel_count += 1
# Print the number of kernels found
    return kernel_count, thresh

def detect(image):
    
    weights_path = Path(r"C:\Users\Personal\Desktop\myproject\best.pt") # Provide the path to your weights file
    model = torch.hub.load('ultralytics/yolov5', 'custom' , path=weights_path)
    
    # Perform inference
    results = model(image)

    # Display results
    results.show()

    # Save results
    results.save(Path("output"))

# Optionally, save annotated image
    annotated_img = results.render()[0]
    #cv2.imwrite("output/annotated_image.jpg", annotated_img)
    
    return annotated_img


@app.route('/')
def index():
    
    return render_template('main.html')


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method =='POST':
        username = request.form['name']
        email = request.form['email']
        organization = request.form['organization']
        address = request.form['address']
        mobilenumber = request.form['phone']
        password = request.form['password']
        country = request.form['country']
        city = request.form['city']
        confirm_password = request.form['confirm_password']
        
        db, cursor = get_db()
        
        cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Username or email is already taken. Please choose another one.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match')            
        else:
            # Insert the new user into the database
            cursor.execute('''
                INSERT INTO users (username, email, organization, address, phonenumber, password, country, city)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (username, email, organization, address, mobilenumber, password, country, city))
            db.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        
    return render_template('sign_up.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db, cursor = get_db()

        # Check if the username and password match
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()

        if user:
            # Set the user in the session
            #session['user_id'] = user['id']
            #flash('Login successful!', 'success')
            return redirect(url_for('upload_file'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/upload', methods=['POST','GET'])
def upload_file():
    if request.method == 'POST':
        #time.sleep(3)
        # check if the post request has the file part
        if 'image' not in request.files:
            return render_template('a.html', msg='No file part')
        file = request.files['image']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return render_template('a.html', msg='No selected file')
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            
            image = cv2.imread(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            annotated_img = detect(image)
            #cv2.imwrite("output/annotated_image.jpg", annotated_img)
            #detected_filename = f"detected_{secure_filename(file.filename)}"
            #detected_path = os.path.join(app.config['PROCESS_FOLDER'], detected_filename)
            #cv2.imwrite(detected_path, annotated_img)
            
            # Get the length and width of the image
            width_cm, length_cm, gray = length_width(image)
            #gray_filename = f"gray_{secure_filename(file.filename)}"
            #gray_path = os.path.join(app.config['PROCESS_FOLDER'], gray_filename)
            #cv2.imwrite(gray_path, gray)
            
            count, thresh = kernel_count(image)
            
            detected_filename = f"detected_{secure_filename(file.filename)}"
            detected_path = os.path.join(app.config['PROCESS_FOLDER'], detected_filename)
            cv2.imwrite(detected_path, annotated_img)
            
            gray_filename = f"gray_{secure_filename(file.filename)}"
            gray_path = os.path.join(app.config['PROCESS_FOLDER'], gray_filename)
            cv2.imwrite(gray_path, gray)
            
            contour_filename = f"cont_{secure_filename(file.filename)}"
            contour_path = os.path.join(app.config['PROCESS_FOLDER'], contour_filename)
            cv2.imwrite(contour_path, thresh)
            
            return render_template('a.html', image_file=filename, len=length_cm, wid=width_cm,th=gray_filename,cont = contour_filename, count=count)
    return render_template('a.html')

@app.route('/logout')
def logout():
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)