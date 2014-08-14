#!/usr/bin/env python

from web import app

if __name__ == '__main__':
    if app.debug:
        app.run(host='0.0.0.0', port=8888, debug=True)
    else:
        app.run(host='0.0.0.0', port=8888)
