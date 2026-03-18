-- ====================================================================
-- ZERO-TOUCH PROVISIONING - SEED DATA
-- ====================================================================

BEGIN;

-- 1. Network Devices
INSERT INTO network_devices (hostname, management_ip, device_type) VALUES 
('PE1',  '192.168.50.10', 'PE'),
('POP1', '192.168.10.11', 'POP'),
('POP2', '192.168.10.12', 'POP');

-- 2. Provisioning Networks (ZTP)
INSERT INTO provisioning_networks (device_id, vlan_id, network_cidr, gateway_ip, dhcp_start, dhcp_stop, description) VALUES 
((SELECT device_id FROM network_devices WHERE hostname='POP1'), 991, '10.99.1.0/24', '10.99.1.1', '10.99.1.100', '10.99.1.200', 'ZTP-POP1'),
((SELECT device_id FROM network_devices WHERE hostname='POP2'), 992, '10.99.2.0/24', '10.99.2.1', '10.99.2.100', '10.99.2.200', 'ZTP-POP2');

-- 3. POP WAN Subnets (Service)
INSERT INTO pop_wan_subnets (device_id, network, gateway_ip, vlan_id) VALUES
((SELECT device_id FROM network_devices WHERE hostname='POP1'), '10.1.100.0/24', '10.1.100.1', 100),
((SELECT device_id FROM network_devices WHERE hostname='POP2'), '10.1.200.0/24', '10.1.200.1', 200);

-- 4. Network Ports (POP1 & POP2)
-- Inserting eth0 to eth10 for POP1
INSERT INTO network_ports (device_id, port_name, port_description, status)
SELECT (SELECT device_id FROM network_devices WHERE hostname='POP1'), 'eth' || gs, 'FREE', 'FREE'
FROM generate_series(0, 10) AS gs;

-- Inserting eth0 to eth10 for POP2
INSERT INTO network_ports (device_id, port_name, port_description, status)
SELECT (SELECT device_id FROM network_devices WHERE hostname='POP2'), 'eth' || gs, 'FREE', 'FREE'
FROM generate_series(0, 10) AS gs;

-- 5. LAN Pools
INSERT INTO lan_pools (network) VALUES 
('172.16.30.0/30'), ('172.16.30.4/30'), ('172.16.30.8/30'), ('172.16.30.12/30'), 
('172.16.30.16/30'), ('172.16.30.20/30'), ('172.16.30.24/30'), ('172.16.30.28/30'), 
('172.16.30.32/30'), ('172.16.29.0/29'), ('172.16.29.8/29'), ('172.16.29.16/29'),
('172.16.29.24/29'), ('172.16.29.32/29'), ('172.16.28.0/28'), ('172.16.28.16/28');

-- 6. Customers
INSERT INTO customers (full_name, document_number) VALUES 
('EMPRESA FULANA', '85232374000195'),
('EMPRESA CICLANA', '57007988000138'),
('EMPRESA BELTRANA', '42769576000168');

-- 7. Reserve Ports
UPDATE network_ports SET port_description = '44001', status = 'RESERVED' WHERE device_id = (SELECT device_id FROM network_devices WHERE hostname = 'POP1') AND port_name = 'eth0';
UPDATE network_ports SET port_description = '44002', status = 'RESERVED' WHERE device_id = (SELECT device_id FROM network_devices WHERE hostname = 'POP2') AND port_name = 'eth0';
UPDATE network_ports SET port_description = '44003', status = 'CONNECTED' WHERE device_id = (SELECT device_id FROM network_devices WHERE hostname = 'POP1') AND port_name = 'eth1';

-- 8. Services Insertion
-- Service 1: Empresa Fulana (Awaiting Provisioning)
INSERT INTO services (customer_id, port_id, download_kbit, upload_kbit, required_lan_mask, status) VALUES (
    (SELECT customer_id FROM customers WHERE document_number='85232374000195'),
    (SELECT port_id FROM network_ports WHERE port_description='44001'),
    307200, 153600, 30, 'READY_TO_PROVISION'
);

-- Service 2: Empresa Ciclana (Awaiting Provisioning)
INSERT INTO services (customer_id, port_id, download_kbit, upload_kbit, required_lan_mask, status) VALUES (
    (SELECT customer_id FROM customers WHERE document_number='57007988000138'),
    (SELECT port_id FROM network_ports WHERE port_description='44002'),
    204800, 102400, 29, 'READY_TO_PROVISION'
);

-- Service 3: Empresa Beltrana (Already Active / Restored)
INSERT INTO services (customer_id, port_id, download_kbit, upload_kbit, required_lan_mask, status, wan_ip, wan_gateway, wan_vlan) VALUES (
    (SELECT customer_id FROM customers WHERE document_number='42769576000168'),
    (SELECT port_id FROM network_ports WHERE port_description='44003'),
    102400, 102400, 28, 'ACTIVE',
    '10.1.100.13/29', '10.1.100.9', 100
);

COMMIT;