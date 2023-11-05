import os


class BaseConfig:
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "my_precious"
    BCRYPT_LOG_ROUNDS = 13
    ACCESS_TOKEN_EXPIRATION = 900  # 15 minutes
    REFRESH_TOKEN_EXPIRATION = 2592000  # 30 days
    NUMBER_OF_CONTENT_IN_ANN = 1000 # UPDATE THIS WHEN DEVELOPING ANN
    INSTANTIATE_PROMPT_ANN = False
    TEAMS_TO_RUN_FOR = ["alpha", "beta", "charlie", "delta", "echo", "foxtrot", "golf"]


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    BCRYPT_LOG_ROUNDS = 4

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_TEST_URL")
    BCRYPT_LOG_ROUNDS = 4
    ACCESS_TOKEN_EXPIRATION = 3
    REFRESH_TOKEN_EXPIRATION = 3


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    NUMBER_OF_CONTENT_IN_ANN = 1000
    INSTANTIATE_PROMPT_ANN = True
