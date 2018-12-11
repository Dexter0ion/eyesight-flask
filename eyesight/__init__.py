import os

from flask import Flask, request
from flask_cors import *
import json


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'eyesight.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    CORS(app, support_credentials=True)
    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    #serach query

    @app.route('/search', methods=['GET', 'POST'])
    @cross_origin(supports_credentials=True)
    
    def search():
        params = {'query': request.args.get('query')}
        if params['query'] == 'test':
            persons = [{
                'name': 'david',
                'age': 10
            }, {
                'name': 'black',
                'age': 20
            }]
            print("test")
            return json.dumps(persons)
        return "OK"

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    return app