import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
TOP_LEVEL_DIR = os.path.abspath(os.curdir)


class Config(object):
    """
    Configuration Object which contains access keys to AWS
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = "SECRET"
    S3_BUCKET = "xxx"
    S3_KEY = "xxx"
    S3_SECRET = "xxx+"
    S3_LOCATION = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)
    ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])


class DevelopmentConfig(Config):
    """
    Development Configuration file
    """
    DEVELOPMENT = True
    DEBUG = True
