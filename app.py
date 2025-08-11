import os
from flask import Flask
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.minecraft import mc_bp
from datetime import timedelta
from werkzeug.middleware.proxy_fix import ProxyFix


# Load environment variables from secrets/.env
load_dotenv(dotenv_path='secrets/.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Read from env file
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)


app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

app.config.update(
    PREFERRED_URL_SCHEME="https",
    SESSION_COOKIE_SECURE=True,
    REMEMBER_COOKIE_SECURE=True,
)


app.register_blueprint(auth_bp)
app.register_blueprint(mc_bp)

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development"
    app.run(debug=debug_mode)