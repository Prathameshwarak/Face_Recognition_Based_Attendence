from flask import Flask, render_template, request, jsonify
import cv2
import os
import csv
import numpy as np
from PIL import Image
import pandas as pd
import datetime
import time
from tkinter import Tk, ttk

app = Flask(__name__)


def assure_path_exists(path):
    dir = os.path.dirname(path)
    if not os.path.exists(dir):
        os.makedirs(dir)


def check_haarcascadefile():
    exists = os.path.isfile("haarcascade_frontalface_default.xml")
    return exists


def save_pass(new_pas):
    assure_path_exists("TrainingImageLabel/")
    exists1 = os.path.isfile("TrainingImageLabel/psd.txt")
    if exists1:
        tf = open("TrainingImageLabel/psd.txt", "r")
        key = tf.read()
    else:
        return jsonify(message='Old Password not found'), 400

    op = request.form.get('old_password')
    newp = request.form.get('new_password')
    nnewp = request.form.get('confirm_new_password')

    if op == key:
        if newp == nnewp:
            txf = open("TrainingImageLabel/psd.txt", "w")
            txf.write(newp)
            return jsonify(message='Password Changed Successfully'), 200
        else:
            return jsonify(message='Confirm new password again!!!'), 400
    else:
        return jsonify(message='Wrong Password'), 400


def psw():
    assure_path_exists("TrainingImageLabel/")
    exists1 = os.path.isfile("TrainingImageLabel/psd.txt")
    if exists1:
        tf = open("TrainingImageLabel/psd.txt", "r")
        key = tf.read()
    else:
        return jsonify(message='Password not set!! Please try again'), 400

    password = request.form.get('password')

    if password == key:
        TrackImages()
    else:
        return jsonify(message='Wrong Password'), 400


def TrainImages():
    check_haarcascadefile()
    assure_path_exists("TrainingImageLabel/")
    recognizer = cv2.face_LBPHFaceRecognizer.create()
    harcascadePath = "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(harcascadePath)
    faces, ID = getImagesAndLabels("TrainingImage")
    try:
        recognizer.train(faces, np.array(ID))
    except:
        return "No Registrations, please register someone first!!!"
    recognizer.save("TrainingImageLabel/Trainner.yml")
    res = "Profile Saved Successfully"
    return res


def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    Ids = []
    for imagePath in imagePaths:
        pilImage = Image.open(imagePath).convert('L')
        imageNp = np.array(pilImage, 'uint8')
        ID = int(os.path.split(imagePath)[-1].split(".")[1])
        faces.append(imageNp)
        Ids.append(ID)
    return faces, Ids


def TrackImages():
    check_haarcascadefile()
    assure_path_exists("Attendance/")
    assure_path_exists("StudentDetails/")

    msg = ''
    i = 0
    j = 0
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    exists3 = os.path.isfile("TrainingImageLabel/Trainner.yml")
    if exists3:
        recognizer.read("TrainingImageLabel/Trainner.yml")
    else:
        return "Data Missing, please click on Save Profile to reset data!!"

    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    cam = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_SIMPLEX
    col_names = ['Id', '', 'Name', '', 'Date', '', 'Time']
    exists1 = os.path.isfile("StudentDetails/StudentDetails.csv")
    if exists1:
        df = pd.read_csv("StudentDetails/StudentDetails.csv")
    else:
        return "Details Missing, students details are missing, please check!"

    while True:
        ret, im = cam.read()
        if not ret:
            return "Error capturing image from the camera"

        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray, 1.2, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(im, (x, y), (x + w, y + h), (225, 0, 0), 2)
            serial, conf = recognizer.predict(gray[y:y + h, x:x + w])
            if (conf < 50):
                ts = time.time()
                date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
                timeStamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                aa = df.loc[df['SERIAL NO.'] == serial]['NAME'].values
                ID = df.loc[df['SERIAL NO.'] == serial]['ID'].values
                ID = str(ID)
                ID = ID[1:-1]
                bb = str(aa)
                bb = bb[2:-2]
                attendance = [str(ID), '', bb, '', str(date), '', str(timeStamp)]
            else:
                Id = 'Unknown'
                bb = str(Id)
            cv2.putText(im, str(bb), (x, y + h), font, 1, (255, 255, 255), 2)
        cv2.imshow('Taking Attendance', im)
        if (cv2.waitKey(1) == ord('q')):
            break

    cam.release()
    cv2.destroyAllWindows()

    ts = time.time()
    date = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y')
    exists = os.path.isfile("Attendance/Attendance_" + date + ".csv")
    if exists:
        df = pd.read_csv("Attendance/Attendance_" + date + ".csv")
        c = df.columns.tolist()
        with open("Attendance/Attendance_" + date + ".csv", 'a+') as csvFile1:
            writer = csv.writer(csvFile1)
            writer.writerow(attendance)
        csvFile1.close()
        col_names.append(date)
        attendance = attendance[:2] + attendance[3:] + [str(date)] + [str(timeStamp)]
    else:
        with open("Attendance/Attendance_" + date + ".csv", 'a+') as csvFile1:
            writer = csv.writer(csvFile1)
            writer.writerow(col_names)
            writer.writerow(attendance)
        csvFile1.close()

    return "Attendance Taken Successfully"


@app.route('/')
def home():
    # You need to pass the necessary data to the template
    # For example, you can create a dictionary with the required data
    data = {
        'attendance_data': {
            'rows': [
                # Your data goes here
                {'id': 1, 'name': 'John Doe', 'date': '2024-03-06'},
                {'id': 2, 'name': 'Jane Doe', 'date': '2024-03-06'},
                # Add more rows as needed
            ]
        }
    }

    return render_template('index.html', attendance_data=data)


@app.route('/train_images', methods=['POST'])
def train_images():
    message = TrainImages()
    return jsonify(message=message)


@app.route('/track_images', methods=['POST'])
def track_images():
    TrackImages()
    return "Attendance Tracked"


if __name__ == '__main__':
    app.run(debug=True)
