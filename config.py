import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()   

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Usar DATABASE_URL si está definido (por ejemplo, en producción), si no, usar configuración local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f"postgresql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}"
        f"@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False