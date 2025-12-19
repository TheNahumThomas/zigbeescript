import json
import paho.mqtt.client as mqtt
import time
import requests
import os
import subprocess

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "plug"
TOPIC = f"zigbee2mqtt/{DEVICE_ID}/set"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Failed to connect, return code {rc}")

def ping_ip(ip):

    command = ['ping', '-c', '1', ip]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def check_hardware_link():

    try:
        interfaces = os.listdir('/sys/class/net')
    except Exception:
        return False

    for iface in interfaces:
        if iface == "lo": continue
        try:
            path = f"/sys/class/net/{iface}/carrier"
            if os.path.exists(path):
                with open(path, 'r') as f:
                    if f.read().strip() == "1":
                        return True
        except Exception:
            continue
    return False

def CyclePlug():
    client = None
    try:
        client = mqtt.Client()
        client.on_connect = on_connect

        client.connect(BROKER, PORT, 60)
        client.loop_start()

        time.sleep(1)

        print(f"Turning {DEVICE_ID} OFF...")
        client.publish(TOPIC, json.dumps({"state": "OFF"}))

        time.sleep(10)

        print(f"Turning {DEVICE_ID} ON...")
        client.publish(TOPIC, json.dumps({"state": "ON"}))
        print("Power Cycle Command Sent.")

    except Exception as e:
        print(f"MQTT Error: {e}")

    finally:
        if client:
            time.sleep(1)
            client.loop_stop()
            client.disconnect()

print("Script starting. Checking for physical connection...")
while not check_hardware_link():
    print("No network cable/link detected. Waiting...")
    time.sleep(5)
print("Physical link detected. Starting Watchdog.")


while True:
    try:
        requests.get("https://www.google.com", timeout=5)
        print("Internet Connection OK")
        time.sleep(20)

    except requests.ConnectionError:
        print("No Internet Connection Found. Diagnosing...")

        if not check_hardware_link():
            print("Abort: My own network link is down. (Cable unplugged?)")
            print("Will not cycle router. Waiting for link...")
            time.sleep(5)
            continue

        pc_alive = ping_ip("192.168.1.186")
        
        router_alive = ping_ip("192.168.1.1")

        if router_alive:
            print("Router is reachable but internet is down. ISP Issue likely.")
            time.sleep(60)
        elif pc_alive:
            print("Router unreachable, BUT PC is visible. Local network is up.")
            print("Skipping reboot to prevent disruption.")
            time.sleep(60)
        else:
            print("Router Unreachable. Initiating Power Cycle...")
            CyclePlug()
            
            print("Waiting 2 and a half minutes for router to reboot...")
            time.sleep(150)

    except Exception as e:
        print(f"Unexpected Error: {e}")
        time.sleep(5)