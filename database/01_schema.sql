-- ====================================================================
-- ZERO-TOUCH PROVISIONING - DATABASE SCHEMA
-- ====================================================================

BEGIN;

-- 1. Custom Types (ENUMs)
CREATE TYPE service_status_enum AS ENUM (
    'AWAITING_PORT',
    'READY_TO_PROVISION',
    'PROVISIONING',
    'ACTIVE',
    'SUSPENDED_PARTIAL',
    'SUSPENDED_TOTAL',
    'CANCELLED'
);

-- 2. Tables
CREATE TABLE network_devices (
    device_id SERIAL PRIMARY KEY,
    hostname VARCHAR(50) NOT NULL UNIQUE,
    management_ip VARCHAR(39) NOT NULL,
    device_type VARCHAR(20) NOT NULL
);

CREATE TABLE provisioning_networks (
    network_id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES network_devices(device_id) ON DELETE CASCADE,
    vlan_id INTEGER NOT NULL,
    network_cidr VARCHAR(43) NOT NULL,
    gateway_ip VARCHAR(39) NOT NULL,
    name_server VARCHAR(39) DEFAULT '8.8.8.8',
    dhcp_start VARCHAR(39),
    dhcp_stop VARCHAR(39),
    description VARCHAR(100),
    UNIQUE (device_id, vlan_id) 
);

CREATE TABLE pop_wan_subnets (
    subnet_id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES network_devices(device_id) ON DELETE CASCADE,
    network VARCHAR(43) NOT NULL,
    gateway_ip VARCHAR(39) NOT NULL,
    vlan_id INTEGER NOT NULL
);

CREATE TABLE network_ports (
    port_id SERIAL PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES network_devices(device_id) ON DELETE CASCADE,
    port_name VARCHAR(20) NOT NULL,
    port_description VARCHAR(50) DEFAULT 'FREE',
    status VARCHAR(20) DEFAULT 'FREE',
    UNIQUE (device_id, port_name)
);

CREATE TABLE lan_pools (
    pool_id SERIAL PRIMARY KEY,
    network VARCHAR(43) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'FREE'
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    document_number VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE services (
    service_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    port_id INTEGER REFERENCES network_ports(port_id),
    download_kbit INTEGER NOT NULL,
    upload_kbit INTEGER NOT NULL,
    required_lan_mask INTEGER NOT NULL,
    status service_status_enum DEFAULT 'AWAITING_PORT',
    wan_ip VARCHAR(43),
    wan_gateway VARCHAR(39),
    wan_vlan INTEGER,
    detected_mac_address VARCHAR(17),
    lan_pool_id INTEGER REFERENCES lan_pools(pool_id),
    provisioned_at TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE
);

COMMIT;