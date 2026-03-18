import ipaddress
from app.db.repository import DatabaseRepository
from app.utils.logger import get_logger

log = get_logger('IPAM')

class IPAMService:

    def __init__(self, db_repo):
        self.db = db_repo

    def allocate_lan_subnet(self, required_mask: int):
        conn = self.db.connect()
        if not conn: return None

        try:
            cur = conn.cursor()
            sql = "SELECT pool_id, network FROM lan_pools WHERE status = 'FREE' AND masklen(network) = %s ORDER BY pool_id ASC LIMIT 1"
            cur.execute(sql, (required_mask,))
            data = cur.fetchone()

            if not data:
                return None
            
            pool_id, network = data
            cur.execute("UPDATE lan_pools SET status='ALLOCATED' WHERE pool_id=%s", (pool_id,))
            conn.commit()

            return {"id": pool_id, "network": network}
        except Exception as e:
            log.error(f"Error allocating LAN subnet: {e}")
            return None
        finally:
            self.db.close()
    
    def allocate_resources(self, service_id, customer_name, required_lan_mask, mac_address, device_id):
        log.info(f"Allocating resources for service {service_id} (Customer: {customer_name})")

        conn = self.db.connect()
        if not conn: return None

        try:
            cur = conn.cursor()

            # WAN subnet
            cur.execute("SELECT network, gateway_ip, vlan_id FROM pop_wan_subnets WHERE device_id = %s", (device_id,))
            subnet_data = cur.fetchone()

            if not subnet_data:
                log.error(f"No available WAN subnet found for device {device_id}.")
                return None
            
            wan_net_cidr, wan_gw, wan_vlan = subnet_data

            # WAN calculations
            net_obj = ipaddress.IPv4Network(wan_net_cidr)
            new_ip_int = int(net_obj.network_address) + 10 + int(service_id)
            new_wan_ip = f"{ipaddress.IPv4Address(new_ip_int)}/{net_obj.prefixlen}"

            # LAN subnet
            lan_data = self.allocate_lan_subnet(required_lan_mask)
            if not lan_data:
                return None
            
            # save allocations on DB
            sql_update = """
            UPDATE services 
            SET wan_ip = %s, wan_gateway = %s, wan_vlan = %s, 
                lan_pool_id = %s, detected_mac_address = %s,
                status = 'PROVISIONING'
            WHERE service_id = %s
            """
            cur.execute(sql_update, (new_wan_ip, wan_gw, wan_vlan, lan_data['id'], mac_address, service_id))
            conn.commit()

            log.info(f"Resources allocated for service {service_id}: WAN IP {new_wan_ip}, LAN Pool {lan_data['network']}")

            return {
                "ip": new_wan_ip, "gw": wan_gw, "vlan": wan_vlan,
                "name": customer_name, "id": service_id, "lan_net": lan_data['network']
            }
        except Exception as e:
            log.error(f"Error allocating resources for service {service_id}: {e}")
            return None
        finally:            
            self.db.close()

    def get_client_data(self, port_desc, mac_address):
        log.info(f"Consulting costumer data for port {port_desc} and MAC {mac_address}...")
        conn = self.db.connect()
        if not conn: return None

        try:
            cur = conn.cursor()
            sql = """
            SELECT s.service_id, s.status, s.wan_ip, s.wan_gateway, s.wan_vlan, 
                   p.network, c.full_name, s.required_lan_mask, np.device_id,
                   s.download_kbit, s.upload_kbit
            FROM services s
            JOIN network_ports np ON s.port_id = np.port_id
            JOIN customers c ON s.customer_id = c.customer_id
            LEFT JOIN lan_pools p ON s.lan_pool_id = p.pool_id
            WHERE np.port_description = %s 
            """
            cur.execute(sql, (port_desc,))
            res = cur.fetchone()

            if not res:
                log.warning(f"No service found for port {port_desc}.")
                return None
            
            log.info(f"Service data found for port {port_desc}: Service ID {res[0]}, Status {res[1]}")
            return {
                "id": res[0], "status": res[1],
                "wan_ip": res[2], "wan_gw": res[3], "wan_vlan": res[4],
                "lan_net": res[5], "name": res[6], "req_mask": res[7],
                "device_id": res[8], "download": res[9], "upload": res[10]
            }
        finally:
            self.db.close()