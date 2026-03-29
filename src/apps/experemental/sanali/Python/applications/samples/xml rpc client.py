import base64
import xmlrpc.client

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Create an XML-RPC client
with xmlrpc.client.ServerProxy("https://31e4-35-199-144-44.ngrok-free.app/RPC2") as proxy:
    res = proxy.pow(2, 3)
    print(res)
