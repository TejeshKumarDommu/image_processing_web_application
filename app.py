from flask import Flask, render_template, request, redirect
import cv2
import os

app = Flask(__name__)

app.config['IMAGE_UPLOADS'] = "C:\\Users\Personal\myproject\static\Image"

from werkzeug.utils import secure_filename

@app.route("/home", methods=["POST","GET"])
def upload_image():
    if request.method == "POST":
        #print(request.files)
        image = request.files['file']
        
        if image.filename == '':
            print("File name is invalid")
            return redirect(request.url)
        
        filename = secure_filename(image.filename)
        
        basedir = os.path.abspath(os.path.dirname(__file__))
        image.save(os.path.join(basedir,app.config['IMAGE_UPLOADS'],filename))
        
        return render_template("a.html")
    
    return render_template("a.html")

@app.route("/display/filename>")
@app.route("/display/filename>")
def display_image():

    return redirect(  url_for('static',filename='/Image/'+filename)  , code=301)

if __name__ == "__main__":
    app.run(port=5000)