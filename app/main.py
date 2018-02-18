from __future__ import print_function
from flask import render_template, redirect, url_for, request, g, session

import os, boto3, io, shutil
from PIL import Image
import shutil
from app import webapp


@webapp.route('/',methods=['GET'])
@webapp.route('/index',methods=['GET'])
@webapp.route('/main',methods=['GET'])
# Display an HTML page with links
def main():
    return render_template("main.html",title="Landing Page")

@webapp.route('/dataform', methods= ['GET'])
def data_form():
    return render_template("data_form.html")

@webapp.route('/image', methods= ['GET'])

def image():
    m = None
# check if the post request has the file part
    if 'image_file' not in request.files:
        m = "Missing uploaded file"
        return render_template("result.html", message = m)
    new_file = request.files['image_file']
# if user does not select file, browser also
# submit a empty part without filename
    if new_file.filename== '' :
        m = 'Missing file name'
        return render_template( "result.html",message = m)

    attempted_name = request.form.get('name','')
    if attempted_name == '':
        m = 'Missing face name'
        return render_template("result.html", message = m)

#create proper file path for storing the image
    fname = os.path.join('app/static', new_file.filename)
    new_file.save(fname)
# upload object to S3
    s3 = boto3.resource('s3')
    image= (fname, attempted_name)
    file = open(image[0], 'rb')
    object = s3.Object('rekog11','index/' + image[0])
    ret = object.put(Body=file, Metadata={ 'FullName':image[1]})
    m = 'Successfully uploaded'
    path = 'app/static/' + new_file.filename
    os.remove(path)

    return render_template("result.html" , message = m)


@webapp.route('/run_form', methods= ['GET'])
def run_form():
    return render_template("run_form.html")


@webapp.route('/imagerun', methods= ['GET', 'POST'])
def image_run():
    m = None
    # check if the post request has the file part
    if 'image_file' not in request.files:
        m = "Missing uploaded file"
        return render_template("result.html",message = m)
    new_file = request.files['image_file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if new_file.filename == '':
        m = 'Missing file name'
        return render_template("result.html", message = m)

    fname = os.path.join('app/static/test', new_file.filename)
    new_file.save(fname)

    rekognition = boto3.c1ient('rekognition', region_name= 'us-east-1')
    dynamodb = boto3.c1ient('dynamodb',region_name= 'us-east-1')
    image = Image.open(fname)
    stream = io.BytesIO()
    image.save(stream, format="JPEG")
    image_binary = stream.getvalue()
    response = rekognition.detect_faces(
        Image={'Bytes': image_binary} )
    all_faces = response['FaceDetails']

    # Initialize list object
    boxes = []
    # Get image diameters
    image_width = image.size[0]
    image_height = image.size[1]
    # Crop face from image
    for face in all_faces:
        box = face['BoundingBox']
        x1 = int(int(box['Left'] * image_width) * 0.9)
        y1 = int(int(box['Top'] * image_height) * 0.9)
        x2 = int(int(box['Left'] * image_width + box['Width'] * image_width) * 1.10)
        y2 = int(int(box['Top'] * image_height + box['Height'] * image_height) * 1.10)
        image_crop = image.crop((x1, y1, x2, y2))

        stream = io.BytesIO()
        image_crop.save(stream, format = "JPEG")
        image_crop_binary = stream.getvalue()

        # Submit individually cropped image to Amazon Rekognition
        response = rekognition.search_faces_by_image(
            CollectionId= 'family_collection', Image={'Bytes': image_crop_binary}
        )
        confidence = []
        name = None

        if len(response['FaceMatches']) > 0:
            # Return results
            # print( 'Coordinates \ box)
            for match in response['FaceMatches']:
                face = dynamodb.get_item(TableName='family_collection', Key={'Rekognitionld': {'S': match['Face']['Faceld']}}
        )
            if 'Item' in face:
                person = face['Item']['FullName']['S']
            else:
                m = 'No Match Found'
                return render_template("result.html" , message = m)

        # print(match[ ' Face' ][ ' Faceld' ], match[' Face']['Confidence' ], person)
            confidence.append(match['Face']['Confidence'])
            if match['Face']['Confidence'] == max(confidence):
                name = person
            else:
                m = 'No Match Found'
                return render_template("result.html", message = m)

    m = 'This is ' + name
    shutil.rmtree('app/static/test')
    os.makedirs('app/static/test')
    return render_template("result.html", message = m)
