import boto3
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import requests
from constant.serverapi import *
app = Flask(__name__, instance_relative_config=True)
app.config.from_object("config.DevelopmentConfig")
bootstrap = Bootstrap(app)

import tools

ALLOWED_EXTENSIONS = app.config["ALLOWED_EXTENSIONS"]


def allowed_file(filename):
    """
    Check allowed file types (jpeg, jpeg)
    :param filename:
    :return:
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_username_from_file(filename):
    """
    Get Username from a file
    :param filename:
    :return:
    """
    return filename.rsplit('.', 1)[0].lower().replace("_", " ")


@app.route("/", methods=['GET', 'POST'])
def index():
    """
    Index API - Returns to Upload template
    :return:
    """
    response = requests.get(server_url + 'patient/get_all_patients')
    patient_list = response.json()
    if request.method == 'POST':
        # There is no file selected to upload
        if "user_file" not in request.files:
            return "No user_file key in request.files"

        file = request.files["user_file"]

        # There is no file selected to upload
        if file.filename == "":
            return "Please select a file"

        # File is selected, upload to S3 and show S3 URL
        if file and allowed_file(file.filename):
            file.filename = secure_filename(file.filename)
            output = tools.supload_file_to_s3(file, app.config["S3_BUCKET"])
            return str(output)
    else:
        return render_template("upload.html", patient_list=patient_list)


@app.route("/upload", methods=['GET', 'POST'])
def train_network():
    """
    Upload endpoint trains the AWS Recognition with User information
    This endpoint uses to register user's faces
    :return:
    """
    if request.method == "POST":

        en_patient_email = request.form["patientemail"].strip()

        if not en_patient_email:
            return "Enter patient email"

        if "userimage" not in request.files:
            return "Select image of you"

        file = request.files["userimage"]

        if file.filename == "":
            return "Select image of you"

        file = request.files["userimage"]

        if file and allowed_file(file.filename):
            file.filename = secure_filename(file.filename)
            output = tools.upload_file_to_s3(file, app.config["S3_BUCKET"])
            res = tools.index_faces(app.config["S3_BUCKET"], file.filename, "my-collection-id", make_file_name(en_patient_email))

            face_id = res[0].get("Face").get("FaceId")

            response_register_face = requests.post(
                server_url + 'patient/create_facial_record', json={
                    'face_id': face_id,
                    'patient_email': en_patient_email
                })
            response_register_face = response_register_face.json()

            status = response_register_face.get("Status")

            if status == "SUCCESS":
                referer = request.referrer
                return render_template('upload_success.html', referer=referer)

            else:
                referer = request.referrer
                return render_template('face_not_found.html', referer=referer)

    else:
        return render_template("compare.html")


@app.route("/compare", methods=['GET', 'POST'])
def compare():
    """
    This endpoints compares the image with the images in the recognition collection
    :return:
    """
    if request.method == "POST":
        appointment_id = request.form['appointment_id']

        if "userimage" not in request.files:
            return "Select image of you"

        file = request.files["userimage"]

        if file.filename == "":
            return "Select image of you"

        file = request.files["userimage"]

        if file and allowed_file(file.filename):
            file.filename = secure_filename(file.filename)
            tools.upload_file_to_s3(file, app.config["S3_BUCKET"])

            try:
                face_response = tools.search_faces_by_image(app.config["S3_BUCKET"], file.filename, "my-collection-id")
            except Exception as e:
                return "Upload an image with clear face view..."

            for record in face_response:
                face = record['Face']
                print("Matched Face ({}%)".format(record['Similarity']))
                print("FaceId : {}".format(face['FaceId']))
                print("ImageId : {}".format(face['ExternalImageId']))

                ex_image_id = make_username_from_image_id(face['ExternalImageId'])

                face_id = face['FaceId']
                response_mark_patient_visited_by_facial = requests.post(server_url + 'patient/mark_patient_visited_by_facial', json={
                    'face_id': face_id,
                    'appointment_id': appointment_id
                })
                response_mark_patient_visited_by_facial = response_mark_patient_visited_by_facial.json()
                if response_mark_patient_visited_by_facial.get('Status') == "INVALID_APPOINTMENT_ID":
                    invalid_appointment_id = "Invalid Appointment ID"
                    return render_template('no_match_found.html', result=invalid_appointment_id)
                elif response_mark_patient_visited_by_facial.get('Status') == "NO_RECORD_FOR_FACIAL_ID":
                    no_record_for_facial_id = "No Record for Facial ID"
                    return render_template('no_match_found.html', result=no_record_for_facial_id)
                elif response_mark_patient_visited_by_facial.get('Status') == "INVALID_DOCTOR_EMAIL":
                    invalid_doctor_email = "Invalid Doctor Email"
                    return render_template('no_match_found.html', result=invalid_doctor_email)
                elif response_mark_patient_visited_by_facial.get('Status') == "INVALID_PATIENT_EMAIL":
                    invalid_patient_email = "Invalid Patient Email"
                    return render_template('no_match_found.html', result=invalid_patient_email)
                elif response_mark_patient_visited_by_facial.get('Status') == "APPOINTMENT_NOT_BELONG_TO_THE_PATIENT":
                    not_belong_to_patient = "Appointment not belongs to the Patient"
                    return render_template('no_match_found.html', result=not_belong_to_patient)
                else:
                    return render_template("user_found.html", user_name=ex_image_id)

    else:
        return render_template("compare.html")


@app.route("/delete")
def delete_collection():
    """
    This endpoint use to delete the existing Rekognition collection
    :return:
    """
    collection_id = 'my-collection-id'
    print('Attempting to delete collection ' + collection_id)
    client = boto3.client('rekognition')
    try:
        response = client.delete_collection(CollectionId=collection_id)
    except Exception as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print('The collection ' + collection_id + ' was not found ')
            return "Collection was not found"
        else:
            print('Error other than Not Found occurred: ' + e.response['Error']['Message'])
            return "Error occurred while deleting collection"
    return "Collection Delete Successful"


@app.route("/create")
def create_new_collection():
    """
    This endpoint uses to create new Recognition collection
    :return:
    """
    collection_id = 'my-collection-id'
    client = boto3.client('rekognition')
    print('Creating collection:' + collection_id)
    response = client.create_collection(CollectionId=collection_id)
    print('Collection ARN: ' + response['CollectionArn'])
    print('Status code: ' + str(response['StatusCode']))
    return "Successfully created a new collection"


def make_file_name(entered_username):
    """
    This method uses to make file name using the entered username
    :param entered_username:
    :return:
    """
    return entered_username.strip().replace(" ", "_").replace("@", "").replace(".com", "")


def make_username_from_image_id(image_id):
    """
    This method uses to make the user name from the image id
    :param image_id:
    :return:
    """
    return image_id.replace("_", " ").upper()


if __name__ == '__main__':
    # host = os.popen('hostname -I').read()
    app.run(port=8000)
    # app.run()
