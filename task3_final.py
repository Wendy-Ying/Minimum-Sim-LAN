from ee315_24_lib import SwitchFabric, Packet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
import re

# 生成AES密钥
def generate_aes_key():
    return os.urandom(16)  # 生成32字节的随机密钥

# AES 加密函数
def aes_encrypt(key, message):
    # 使用 PKCS7 填充消息，确保消息长度是 AES 块大小的倍数
    padder = padding.PKCS7(128).padder()
    padded_message = padder.update(message.encode()) + padder.finalize()
    
    # 生成随机的 IV（初始化向量）
    iv = os.urandom(16)
    
    # 设置 AES 密码器，使用 CBC 模式
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # 加密填充后的消息
    encrypted_message = encryptor.update(padded_message) + encryptor.finalize()
    
    # 返回 IV 和加密后的消息（IV + 加密消息）
    return iv + encrypted_message

# AES 解密函数
def aes_decrypt(key, encrypted_message):
    # 提取 IV（前 16 字节）和加密消息
    iv = encrypted_message[:16]
    encrypted_message = encrypted_message[16:]
    
    # 设置 AES 解密器，使用 CBC 模式
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    # 解密消息
    padded_message = decryptor.update(encrypted_message) + decryptor.finalize()
    
    # 去除填充
    unpadder = padding.PKCS7(128).unpadder()
    
    try:
        message = unpadder.update(padded_message) + unpadder.finalize()
        return message.decode()  # 解码为字符串
    except ValueError as e:
        return None

def string2digital(message):
    return list(message)

# 将数字转换为字节串（数字负载）
def digital2string(digital_payload):
    return bytes(digital_payload)

class Host:
    def __init__(self, mac, interface, key):
        if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac):
            raise ValueError("Invalid MAC address format")
        self.mac = mac
        self.interface = interface
        self.buffer = []
        self.aes_key = key

    def send_packet(self, dest_mac, message, switch):
        print()
        print(f"Initial Message: '{message}'")
        encrypted_message = aes_encrypt(self.aes_key, message)  # 加密消息
        digital_payload = string2digital(encrypted_message)  # 转换为数字负载
        print(f"Encrypted Message: {encrypted_message}")
        print(f"Transmission Message: {digital_payload}")
        
        packet = Packet(self.mac, dest_mac, digital_payload)
        switch.handle_packet(packet)  # 通过交换机发送数据包
        switch.add_mac(self.mac, self.interface)

    def receive_packet(self, packet):
        if packet.dst == self.mac:
            byte_payload = digital2string(packet.payload)  # 转换为字节串
            
            # 解密消息
            decrypted_payload = aes_decrypt(self.aes_key, byte_payload)  # 解密数字负载
            
            if decrypted_payload:
                self.buffer.append(decrypted_payload)
                print(f"Received and Recovered Message: '{decrypted_payload}'")
            else:
                print("Failed to decrypt the packet.")

class Switch:
    def __init__(self, fabric, num_interfaces=8):
        self.num_interfaces = num_interfaces
        self.interfaces = {}
        self.mac_table = {}
        self.mac = {}
        self.fabric = fabric
        self.firewall_rules = []  # 新增防火墙规则列表
        for i in range(self.num_interfaces):
            self.interfaces[i] = None

    def add_firewall_rule(self, rule):
        self.firewall_rules.append(rule)
        print()
        print(f"Firewall rule added: {rule}")

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

        # Check firewall rules before forwarding
        if self.check_firewall(packet):
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
        else:
            print(f"Firewall blocked packet from {src_mac} to {dst_mac}")

    # key changes here
    def add_mac(self, mac, interface):
        # delete the old interface
        old_mac = self.get_mac_for_interface(interface)
        if old_mac!= mac and old_mac != None:
            del self.mac[old_mac]
            del self.mac_table[old_mac]
            print(f"Deleted interface {interface} from mac {mac}")
        # delete the old mac
        if mac in self.mac:
            del self.mac[mac]
            del self.mac_table[mac]
            print(f"Deleted MAC {mac} from interface {interface}")
        self.mac[mac] = interface
        print(f"Switch added MAC {mac} to interface {interface}")

    def get_mac_for_interface(self, interface):
        for mac, intf in self.mac.items():
            if intf == interface:
                return mac
        return None

    def print_mac(self):
        print()
        print("Current MAC address to interface mapping:")
        for mac, interface in self.mac.items():
            print(f"MAC: {mac} -> Interface: {interface}")
            
    def check_firewall(self, packet):
        # 默认允许所有数据包通过
        allowed = True
        for rule in self.firewall_rules:
            if rule['action'] == 'block':
                # 如果规则中包含 src_mac，则检查源MAC地址
                if 'src_mac' in rule and rule['src_mac'] == packet.src:
                    allowed = False
                    break
                # 如果规则中包含 dst_mac，则检查目的MAC地址
                if 'dst_mac' in rule and rule['dst_mac'] == packet.dst:
                    allowed = False
                    break
        return allowed

# 创建网络
shared_fabric = SwitchFabric()
switch = Switch(shared_fabric)

# 生成AES密钥
key = generate_aes_key()

# 创建主机
host1 = Host("00:00:00:00:00:01", 0, key)
host2 = Host("00:00:00:00:00:02", 1, key)
host3 = Host("00:00:00:00:00:03", 2, key)

# 连接主机到交换机
shared_fabric.connect_host_to_switch(host1, switch)
shared_fabric.connect_host_to_switch(host2, switch)
shared_fabric.connect_host_to_switch(host3, switch)

# 模拟通信
host1.send_packet("00:00:00:00:00:02", "Hello from A", switch)
host2.send_packet("00:00:00:00:00:03", "Hello from B", switch)
host3.send_packet("00:00:00:00:00:01", "Hello from C", switch)

# 添加新的MAC地址
host4 = Host("00:00:00:00:00:04", 1, key)
shared_fabric.connect_host_to_switch(host4, switch)
host4.send_packet("00:00:00:00:00:03", "Hello from D", switch)

# 添加新的接口
host5 = Host("00:00:00:00:00:03", 3, key)
shared_fabric.connect_host_to_switch(host5, switch)
host5.send_packet("00:00:00:00:00:01", "Hello from E", switch)

# 添加防火墙规则，阻止00:00:00:00:00:04的通信
switch.add_firewall_rule({'action': 'block', 'dst_mac': '00:00:00:00:00:04'})
host1.send_packet("00:00:00:00:00:04", "Hello from A", switch)  # 这个包将被防火墙阻止

# 打印当前的MAC地址到接口映射
switch.print_mac()