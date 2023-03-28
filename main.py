from app.server import socketio
from app.server import app
from os import getenv

if __name__ == '__main__':
    PORT = getenv('PORT') or 80
    DEBUG = getenv('DEBUG') or False
    print('Starting server on port {}'.format(PORT))
    socketio.run(app, debug=DEBUG, use_reloader=False, port=PORT)