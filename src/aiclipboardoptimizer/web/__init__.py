"""Web interface for Token Optimizer using Flask + React."""
from flask import Flask
from flask_cors import CORS


def create_app(config=None):
    """Application factory for Flask app."""
    app = Flask(__name__)

    # Enable CORS for React frontend
    CORS(app)

    # Load config
    if config:
        app.config.update(config)

    # Register blueprints
    from .routes import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}

    return app
