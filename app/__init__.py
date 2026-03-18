from flask import Flask

def create_app():
    app = Flask(__name__)
    
    from app.routes.ztp_routes import ztp_bp
    
    app.register_blueprint(ztp_bp)
    
    return app