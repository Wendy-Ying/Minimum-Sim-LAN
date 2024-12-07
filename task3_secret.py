from ee315_24_lib import SwitchFabric, Packet

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
import re

# 生成AES密钥
def generate_aes_key():
    return os.urandom(32)  # 生成32字节的随机密钥

# AES加密
def aes_encrypt(key, message):
    padder = padding.PKCS7(128).padder()
    padded_message = padder.update(message.encode()) + padder.finalize()
    iv = os.urandom(16)  # 生成16字节的随机初始化向量
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_message = encryptor.update(padded_message) + encryptor.finalize()
    return iv + encrypted_message  # 返回IV和加密消息的组合

# AES解密
def aes_decrypt(key, encrypted_message):
    iv = encrypted_message[:16]  # 提取IV
    encrypted_message = encrypted_message[16:]  # 提取加密消息
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_message = decryptor.update(encrypted_message) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    message = unpadder.update(padded_message) + unpadder.finalize()
    return message.decode()

class Host:
    def __init__(self, mac, interface):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []
        self.aes_key = generate_aes_key()  # 使用AES密钥

    def send_packet(self, dst_mac, payload, switch):
        print(f"Host {self.mac} sending payload: '{payload}'")
        encrypted_payload = aes_encrypt(self.aes_key, payload)
        print(f"Host {self.mac} encrypted payload: {encrypted_payload}")
        print(f"Encrypted payload length: {len(encrypted_payload)}")
        packet = Packet(self.mac, dst_mac, encrypted_payload)
        switch.handle_packet(packet)

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            print(f"Host {self.mac} received encrypted packet: {packet.payload}")
            print(f"Received payload length: {len(packet.payload)}")
            decrypted_payload = aes_decrypt(self.aes_key, packet.payload)
            if decrypted_payload:
                self.buffer.append(decrypted_payload)
                print(f"Host {self.mac} decrypted payload: '{decrypted_payload}'")
            else:
                print("Failed to decrypt the packet.")

class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.fabric = fabric
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

    def handle_packet(self, packet):
        # Learn the source MAC address and store the interface number
        src_mac = packet.src
        dst_mac = packet.dst

        # Check if the source MAC is already in the MAC table
        if src_mac not in self.mac_table:
            # Learn the source MAC address and associate it with the incoming interface
            self.mac_table[src_mac] = 0
            print(f"Switch learned MAC {src_mac}")
        else:
            self.mac_table[src_mac] = 1
            
        # Selective forwarding or flooding
        if dst_mac in self.mac_table:
            # Forward to the known destination interface
            dst_interface = None
            for interface, mac in self.fabric.physical_map.items():
                if mac == dst_mac:
                    dst_interface = interface
                    break
            self.mac_table[dst_mac] = 1
            print(f"Switch forwarding packet to known interface {dst_interface}")
            self.fabric.forward_to_interface(packet, dst_interface)
        else:
            # Update the MAC table with the new interface
            self.mac_table[dst_mac] = 1
            # Flood to all interfaces except the incoming one
            print(f"Switch flooding packet to all interfaces")
            for i, host in self.interfaces.items():
                if host and i != src_mac:
                    self.fabric.forward_to_interface(packet, i)

# 创建网络
shared_fabric = SwitchFabric()
switch = Switch(shared_fabric)

# 共享密钥
shared_aes_key = generate_aes_key()

host1 = Host("00:00:00:00:00:01", 0)
host2 = Host("00:00:00:00:00:02", 1)
host3 = Host("00:00:00:00:00:03", 2)

# 设置所有主机使用相同的密钥
host1.aes_key = shared_aes_key
host2.aes_key = shared_aes_key
host3.aes_key = shared_aes_key

# 连接主机到交换机
shared_fabric.connect_host_to_switch(host1, switch)
shared_fabric.connect_host_to_switch(host2, switch)
shared_fabric.connect_host_to_switch(host3, switch)

# 模拟通信
host1.send_packet("00:00:00:00:00:02", "Hello from A", switch)
host2.send_packet("00:00:00:00:00:03", "Hello from B", switch)
host1.send_packet("00:00:00:00:00:03", "Hello from A", switch)
host3.send_packet("00:00:00:00:00:01", "Hello from C", switch)
host3.send_packet("00:00:00:00:00:02", "Hello from C", switch)