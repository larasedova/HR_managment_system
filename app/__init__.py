from flask import Flask
from app.config import Config
from app.models import db


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Инициализация базы данных
    db.init_app(app)

    # Регистрация маршрутов
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
