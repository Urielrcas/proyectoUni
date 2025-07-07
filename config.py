import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_larga_y_aleatoria_para_tu_app'

    # Cadena de conexión a MongoDB Atlas
    MONGO_URI = os.environ.get('MONGO_URI') or \
        'mongodb+srv://ur81730:1234@m0.1kt2sc6.mongodb.net/?retryWrites=true&w=majority&appName=M0'

    # Nombre de la base de datos que vas a usar
    MONGO_DBNAME = 'gestor_de_tareas_'

    # Carpeta para subir imágenes
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
