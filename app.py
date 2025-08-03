import os
from flask import Flask
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.minecraft import mc_bp
from datetime import timedelta

# Load environment variables from secrets/.env
load_dotenv(dotenv_path='secrets/.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Read from env file

app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

app.register_blueprint(auth_bp)
app.register_blueprint(mc_bp)

if __name__ == "__main__":
    app.run(debug=True)
