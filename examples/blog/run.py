from blog import app
from pumpkin.server import WerkzeugServer

if __name__ == '__main__':
    app.run(DEBUG=True)