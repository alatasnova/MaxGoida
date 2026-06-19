import base64
from flask import Flask, Blueprint, Response, send_file
from configs.configs import Configs


def encode_64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")

app = Flask(__name__)

title = "MaxGoida"
update_interval: int = 1  # in hours
configs: Configs = Configs(["hysteria2://c6b2924e-a913-4864-a910-b446b9841b4b@167.104.219.219:443?security=tls&sni=connect-tr1.gadmap.online#%F0%9F%8C%90%20Anycast-IP%20%7C%20%F0%9F%87%B9%F0%9F%87%B7%20%F0%9F%87%BA%F0%9F%87%B8%20%7C%20[BL]",
           "vless://394f6981-a782-4779-9a85-e6cf22935d93@45.159.12.161:8443?encryption=none&security=tls&sni=ams1.fromblancwithlove.com&fp=chrome&packetEncoding=xudp#%F0%9F%87%B8%F0%9F%87%AA%20Sweden,%20Stockholm%20%7C%20[BL]"])

def generate_response():
    resp = [
        f"# profile-title: {title}",
        f"# profile-update-interval: {update_interval}",
        '',
        *configs.configs_list
    ]

    return '\n'.join(resp)

@app.route('/')
def handle_fetch():
    return Response(generate_response(), mimetype='text/plain')

@app.route('/alt')
def handle_fetch_alt():
    return send_file('static/configs.txt', mimetype='text/plain')

app.run('0.0.0.0', debug=True)