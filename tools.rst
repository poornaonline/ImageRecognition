Tools
=====

- def upload_file_to_s3(file, bucket_name, acl="public-read") - (Upload files to the S3 to analyze images)
- def search_faces_by_image(bucket, key, collection_id, threshold=80, region="us-east-1") - (Search Faces by image from the Rekognition collection)
- def index_faces(bucket, key, collection_id, image_id=None, attributes=(), region="us-east-1") - (Index faces with the image id in a collection by Rekognition to analyze and recognize the face)