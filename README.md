# Image-Recognition-Web-Application-using-AWS

## Features

* S3 bucket for image storage (used during upload of new image to be added to the face collection)
* DynamoDB database used to keep track of RekognitionID of stored faces and their corresponding names.
* Lambda function is designed to be triggered when an upload is done to a specific folder inside the S3 bucket.
* Amazon Rekognition is used to recognize and add new face data to the collection.
