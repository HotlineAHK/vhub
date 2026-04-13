from flask import Flask
from api import get_servers

app = Flask(__name__)

@app.route('/')
def get_subscription_servers():
    return get_servers()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5100)