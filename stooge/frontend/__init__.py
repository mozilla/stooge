# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

from flask import Flask
app = Flask(__name__);

from stooge.frontend import views
from stooge.frontend.util import CustomJSONEncoder

def configure_app(app, filename):
    app.json_encoder = CustomJSONEncoder
    if not filename:
        app.config.from_object('stooge.frontend.config.DefaultConfig')
    else:
        app.config.from_pyfile(filename)
    return app
