import http.client
import json

# Fuzzy Server
# REQUIRES NCSU VPN OR EDUROAM
HOST, PORT = "bunyan.csc.ncsu.edu", 5001
# HOST, PORT = "127.0.0.1", 8081
_conn = None


# Function to query the server
def _get(path):
    global _conn
    if _conn is None:
        _conn = http.client.HTTPConnection(HOST, PORT)
    try:
        _conn.request("GET", path)
        return json.loads(_conn.getresponse().read())
    except (http.client.HTTPException, ConnectionError):
        _conn = http.client.HTTPConnection(HOST, PORT)
        _conn.request("GET", path)
        return json.loads(_conn.getresponse().read())


def next_statement(unityid, seed, reset=False):
    """Constructs the API request path with parameters and queries the fuzzy server.
    
        Parameters:
            unityid (str): Your NCSU Unity ID used to track your session or experiment.
            seed (str): Random seed for reproducible statements.
            reset (bool): If True, resets the fuzzy statment generator. Defaults to False.
    
        Returns:
            command (str): Fuzzy logic statement
        """
    return _get(f"/?unityid={unityid}&seed={seed}&reset={str(reset).lower()}")["command"]