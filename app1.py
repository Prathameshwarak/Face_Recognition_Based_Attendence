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
        TrainImages()
    else:
        return jsonify(message='Wrong Password'), 400

@app.route('/take_images', methods=['POST'])
def take_images():
    check_haarcascadefile()
    assure_path_exists("TrainingImage/")

    cam = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Use camera index 1, adjust if needed

    serial = 0
    exists = os.path.isfile("StudentDetails/StudentDetails.csv")
    if exists:
        with open("StudentDetails/StudentDetails.csv", 'r') as csvFile1:
            reader1 = csv.reader(csvFile1)
            for l in reader1:
                serial = serial + 1
        serial = (serial // 2)
        csvFile1.close()
    else:
        with open("StudentDetails/StudentDetails.csv", 'a+') as csvFile1:
            writer = csv.writer(csvFile1)
            writer.writerow(['SERIAL NO.', '', 'ID', '', 'NAME'])
            serial = 1
        csvFile1.close()

    Id = request.form.get('id')
    name = request.form.get('name')

    if name.isalpha() or ' ' in name:
        detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        sampleNum = 0

        while True:
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                sampleNum = sampleNum + 1
                cv2.imwrite(f"TrainingImage/{name}.{serial}.{Id}.{sampleNum}.jpg", gray[y:y + h, x:x + w])

            cv2.imshow('Taking Images', img)

            if cv2.waitKey(100) & 0xFF == ord('q') or sampleNum > 100:
                break

        cam.release()
        cv2.destroyAllWindows()

        row = [serial, '', Id, '', name]
        with open('StudentDetails/StudentDetails.csv', 'a+') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(row)
        csvFile.close()

        message = f"Images Taken for ID: {Id}"
        return jsonify(message=message)
    else:
        message = "Enter Correct name"

        return jsonify(message=message)

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

def TrackImages(tv):
    check_haarcascadefile()
    assure_path_exists("Attendance/")
    assure_path_exists("StudentDetails/")
    for k in tv.get_children():
        tv.delete(k)
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

    display_attendance(tv)

def display_attendance(tv):
    date_for_display = datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y')
    exists = os.path.isfile("Attendance/Attendance_" + date_for_display + ".csv")
    if exists:
        df = pd.read_csv("Attendance/Attendance_" + date_for_display + ".csv")
        col_names = df.columns.tolist()
        tv['columns'] = col_names
        tv.heading("#0", text="Index")
        tv.column("#0", anchor="center", width=40)
        for col in col_names:
            tv.heading(col, text=col)
            tv.column(col, anchor="center", width=80)

        data = df.to_numpy().tolist()
        for i, row in enumerate(data, start=1):
            tv.insert(parent='', index='end', iid=i, values=row)
    else:
        return {'message': 'No data available for the current date!'}

@app.route('/')
def home():
    # Assuming you have a Treeview widget in your HTML template with id 'attendance_tv'
    root = Tk()
    tv = ttk.Treeview(root)
    # Provide the Treeview widget here
    attendance_data = display_attendance(tv)
    if attendance_data is not None:
        return render_template('index1.html', attendance_data=attendance_data)
    else:
        return render_template('index1.html', attendance_data={'message': 'No data available', 'rows': []})

if __name__ == '__main__':
    app.run(debug=True,port=8000)
