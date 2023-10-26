import os
import json
import requests
import pandas as pd
import time
import datetime
import argparse
from io import StringIO

url_base = "http://www.aphanti.com"
reconnect_num = 3
reconnect_dt = 10
retry_vpn = 2
wait_vpn = 20
col_action = "vpn_action"
col_status = "vpn_status"
vpn_dir = ""

def get_cmd(name):
    url = f"{url_base}/media/ips/{name}.csv"
    for i in range(reconnect_num):
        try:
            print(f'{datetime.datetime.now()} getting cmd from {url}')
            res = requests.get(url)
            if res.status_code == 200:
                df = pd.read_csv(StringIO(res.text), dtype=str)
                df = df.fillna('')
                if (col_action in list(df.columns)) and (df.loc[0, col_action] != ""):
                    cmd = df.loc[0, col_action]
                    print(f'cmd: {cmd}')
                    if (cmd == 'start') and (check_vpn_status() == False):
                        for j in range(retry_vpn):
                            print(f'starting vpn, wait for {wait_vpn} seconds...')
                            start_vpn()
                            time.sleep(wait_vpn)
                            if check_vpn_status():
                                print(f'vpn was started successfully!')
                                update_vpn_status(name, "on")
                                break
                    if (cmd == 'stop') and (check_vpn_status() == True):
                        for j in range(retry_vpn):
                            print(f'stopping vpn, wait for {wait_vpn} seconds...')
                            stop_vpn()
                            time.sleep(wait_vpn)
                            if check_vpn_status() == False:
                                print(f'vpn was stopped successfully!')
                                update_vpn_status(name, "off")
                                break

                else:
                    print('no cmd found!')
                return
        except:
            print(f'connection failed! retry in {reconnect_dt} seconds...')
            time.sleep(reconnect_dt)


def update_vpn_status(name, vpn_status):
    url = f"{url_base}/myip?name={name}&vpn_status={vpn_status}"
    for i in range(reconnect_num):
        try:
            print(f'update vpn status: {name} {vpn_status}')
            res = requests.get(url)
            if res.status_code == 200:
                break
        except:
            print(f'connection failed! retry in {reconnect_dt} seconds...')
            time.sleep(reconnect_dt)

def check_vpn_status():
    for i in range(reconnect_num):
        try:
            print('checking vpn_ip and my_ip...')
            vpn_ip = requests.get(f"{url_base}/media/ips/openvpn_server.txt").text.strip()
            my_ip = json.loads(requests.get(f"{url_base}/myip").text)['REMOTE_ADDR']
            print('vpn:', vpn_ip, ', myip:', my_ip)
            if vpn_ip == my_ip:
                return True
            else:
                return False
        except:
            print(f'connection failed! retry in {reconnect_dt} seconds...')
            time.sleep(reconnect_dt)

def stop_vpn():
    os.system("sudo pkill -9 openvpn")
    
def start_vpn():
    os.system(f"nohup sudo openvpn --config {vpn_dir}/openvpn_client.ovpn --auth-user-pass {vpn_dir}/openvpn_userpswd.txt &")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--name", type=str, required=True, help="remote pc name")
    parser.add_argument("-v", "--vpn_dir", type=str, required=True, help="vpn director")
    args = parser.parse_args()

    vpn_dir = args.vpn_dir
    get_cmd(args.name)

