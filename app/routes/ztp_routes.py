from flask import Blueprint, request, Response, jsonify
import threading

from app.config import Config
from app.db.repository import DatabaseRepository
from app.services.discovery_service import DiscoveryService
from app.services.ipam_service import IPAMService
from app.services.workflow_service import WorkflowService
from app.network.vendors.vyos import VyOSVendor
from app.utils.logger import get_logger

log = get_logger("API-ROUTES")

ztp_bp = Blueprint('ztp_routes', __name__)
db_repo = DatabaseRepository()
ipam_service = IPAMService(db_repo)
workflow_service = WorkflowService(db_repo)
vyos_vendor = VyOSVendor()

@ztp_bp.route('/bootstrap', methods=['GET'])
def bootstrap():
    client_ip = request.remote_addr
    print("\n" + "=" * 90)
    log.info(f"Received bootstrap request from {client_ip}")

    try:
        pop_id = int(client_ip.split('.')[2])
        pop_ip = Config.POP_MAP.get(pop_id)
        if not pop_ip:
            raise Exception(f"POP ID {pop_id} not found in configuration")  
        log.info(f"Identified POP ID: {pop_id}, POP IP: {pop_ip}")
    except Exception as e:
        log.error(f"Error processing bootstrap request: {str(e)}")
        return Response("# Error IP Logic", status=400, mimetype='text/plain')
    
    # L2 Discovery
    mac = DiscoveryService.get_mac_from_pe_arp(client_ip)
    if not mac: 
        return Response("# Error MAC", status=500, mimetype='text/plain')

    port, desc = DiscoveryService.get_port_and_desc_from_pop(pop_ip, mac)
    if not port: 
        return Response("# Error Port", status=500, mimetype='text/plain')
    
    # Service discovery 
    data = ipam_service.get_client_data(desc, mac)
    if not data: 
        return Response("# No Contract", status=404, mimetype='text/plain')

    state = data['status']

    if state == 'READY_TO_PROVISION':
        config = ipam_service.allocate_resources(
            data['id'], data['name'], data['req_mask'], mac, data['device_id']
        )
        if not config: 
            return Response("# Alloc Error", status=500, mimetype='text/plain')
        
        log.info(f"Phase 1 started for client {data['name']} with contract ID {data['id']}")
        log.info(f"sending configuration script and waiting CPE reboot...")
        script = vyos_vendor.generate_boot_script(config)
        return Response(script, mimetype='text/plain')
    
    elif state == 'PROVISIONING':
        log.info(f"Phase 2 started for client {data['name']} with contract ID {data['id']}")
        wan_ip_clean = data['wan_ip'].split('/')[0]

        # Threading to avoid blocking the response while provisioning in phase 2
        t = threading.Thread(
            target=workflow_service.phase2_provisioning,
            args=(wan_ip_clean, data['lan_net'], data['id'], data['name'], data['download'], data['upload'])
        )
        t.start()
        
        script = vyos_vendor.generate_silence_script()
        return Response(script, mimetype='text/plain')
    
    elif state == 'ACTIVE':
        log.info(f"Client {data['name']} with contract ID {data['id']} is already active. Sending silence script.")
        return Response("# Already Provisioned", mimetype='text/plain')

    return Response("# Unknown State", status=500, mimetype='text/plain')

@ztp_bp.route('/callback', methods=['POST'])
def callback():
    return jsonify({"status": "ignored"}), 200