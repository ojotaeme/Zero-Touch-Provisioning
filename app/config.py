import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERVER_IP = os.getenv('SERVER_IP', '0.0.0.0')

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "database": os.getenv("DB_NAME", "autoprovisioning"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": os.getenv("DB_PORT", "5432")
    }   

    DEVICE_CREDS = {
        "username": os.getenv("DEVICE_USERNAME", "vyos"),
        "password": os.getenv("DEVICE_PASSWORD", "vyos"),
        "device_type": os.getenv("DEVICE_TYPE", "vyos"),
        "port": int(os.getenv("DEVICE_PORT", 22)),
        "global_delay_factor": 2
    }   

    PE_MGMT_IP = os.getenv("PE_MGMT_IP", "192.168.50.10")

    POP_MAP = {
        1: "192.168.10.11",
        2: "192.168.10.12",
    }