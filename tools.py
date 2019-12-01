import boto3
from app import app

s3 = boto3.client(
    "s3",
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET'],
    region_name='us-east-1'
)


def upload_file_to_s3(file, bucket_name, acl="public-read"):
    """
    Upload files to the S3 to analyze images
    :param file:
    :param bucket_name:
    :param acl:
    :return:
    """
    try:

        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(app.config["S3_LOCATION"], file.filename)


def search_faces_by_image(bucket, key, collection_id, threshold=80, region="us-east-1"):
    """
    Search Faces by image from the Rekognition collection
    :param bucket:
    :param key:
    :param collection_id:
    :param threshold:
    :param region:
    :return:
    """
    rekognition = boto3.client("rekognition", region)
    response = rekognition.search_faces_by_image(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        FaceMatchThreshold=threshold,
    )
    return response['FaceMatches']


def index_faces(bucket, key, collection_id, image_id=None, attributes=(), region="us-east-1"):
    """
    Index faces with the image id in a collection by Rekognition to analyze and recognize the face
    :param bucket:
    :param key:
    :param collection_id:
    :param image_id:
    :param attributes:
    :param region:
    :return:
    """
    rekognition = boto3.client("rekognition", region)
    response = rekognition.index_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        ExternalImageId=image_id,
        DetectionAttributes=attributes,
    )
    return response['FaceRecords']
