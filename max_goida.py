from config_server import ConfigServer


class MaxGoida:
    def __init__(self, server: ConfigServer):
        server.update_configs()