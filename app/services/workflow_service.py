import time
import ipaddress
import subprocess
from app.network.connection import NetworkConnection
from app.network.vendors.vyos import VyOSVendor
from app.db.repository import DatabaseRepository
from app.config import Config
from app.utils.logger import get_logger

log = get_logger("PROVISIONING")

class WorkflowService:

    def __init__(self, db_repo: DatabaseRepository):
        self.db = db_repo
        self.vendor = VyOSVendor()

    def phase2_provisioning(self, wan_ip, lan_net, service_id, cust_name, down_speed, up_speed):
        log.info(f"Starting PHASE 2 provisioning for service {service_id} - {cust_name}")
        time.sleep(15)

        # Config static route on PE router
        self._configure_pe_route(lan_net, wan_ip)

        # Config LAN and QoS on CPE router
        net_obj = ipaddress.IPv4Network(lan_net)
        lan_gw = str(next(net_obj.hosts()))
        lan_prefix = str(net_obj.prefixlen)

        success = False
        for attempt in range(3):
            try:
                if self._configure_cpe_final(wan_ip, lan_gw, lan_prefix, down_speed, up_speed):
                    success = True
                    break
            except Exception as e:
                log.error(f"Attempt {attempt+1}: Failed to configure CPE router - {e}")
                time.sleep(3)

        if success:
            log.info(f"phase 2 configuration commands executed successfully for service {service_id}")

            # Validation 
            log.info(f"Starting validation for service {service_id}")
            if self._validate_ping_from_pe(lan_gw):
                log.info(f"[PASS] Ping PE -> CPE successful for service {service_id}")
            else:
                log.error(f"[FAIL] Ping PE -> CPE failed for service {service_id}")
            if self._validate_ping_local(lan_gw):
                log.info(f"[PASS] Ping ZTP Server -> LAN {lan_gw} successful for service {service_id}")
            else:
                log.warning(f"[FAIL] Ping ZTP Server -> LAN {lan_gw} failed for service {service_id}")
            
            # Save provisioning result to database
            self._mark_service_active(service_id)
        else:
            log.error(f"Failed to execute phase 2 configuration commands after 3 attempts for service {service_id}")
    
    def _configure_pe_route(self, lan_network, cpe_wan_ip):
        commands = [f"set protocols static route {lan_network} next-hop {cpe_wan_ip}"]
        conn = NetworkConnection({"host": Config.PE_MGMT_IP, **Config.DEVICE_CREDS})

        if conn.connect():
            conn.send_config_set(commands)
            conn.disconnect()
            log.info(f"Static route to {lan_network} via {cpe_wan_ip} configured on PE router")
            return True
        return False
    
    def _configure_cpe_final(self, cpe_wan_ip, lan_gw, lan_prefix, down_kbps, up_kbps):

        commands = self.vendor.get_lan_qos_commands(cpe_wan_ip, lan_gw, lan_prefix, down_kbps, up_kbps)

        cpe_creds = Config.DEVICE_CREDS.copy()
        cpe_creds['host'] = cpe_wan_ip

        try:
            conn = NetworkConnection(cpe_creds)
            if conn.connect():
                conn.send_config_set(commands) 
                conn.disconnect()
                return True
        except Exception as e:
            print(f"Failed to configure CPE router - {e}")
            
        return False
    
    def _validate_ping_from_pe(self, target_ip):
        conn = NetworkConnection({"host": Config.PE_MGMT_IP, **Config.DEVICE_CREDS})
        if conn.connect():
            output = conn.send_command(f"ping {target_ip} count 2")
            conn.disconnect()
            if output and "0% packet loss" in output:
                return True
        return False
    
    def _validate_ping_local(self, target_ip):
        response = subprocess.call(['ping', '-n', '2', target_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return response == 0
    
    def _mark_service_active(self, service_id):
        conn = self.db.connect()
        if not conn: return
        try:
            cur = conn.cursor()
            sql = "UPDATE services SET status='ACTIVE', provisioned_at = NOW() AT TIME ZONE 'UTC' - INTERVAL '3 hours' WHERE service_id=%s"
            cur.execute(sql, (service_id,))
            conn.commit()
            log.info(f"Service {service_id} provisioned successfully and marked as ACTIVE in database")
        finally:
            self.db.close()

