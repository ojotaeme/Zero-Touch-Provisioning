from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    print("-" * 60)
    print(" Zero-Touch-Provisioning Sever running ".center(60, "-"))
    print("-" * 60)
    
    app.run(host=Config.SERVER_IP, port=5000)