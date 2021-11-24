import os

from flask import Flask

from finanger.dashboard import brl

def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'finanger.sqlite'),
    )

    app.config.from_pyfile('config.py', silent=True)

    # ensure the instace folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from .dashboard import brl
    app.jinja_env.filters["brl"] = brl

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import dashboard
    app.register_blueprint(dashboard.bp)
    app.add_url_rule('/', endpoint='index')

    from . import accounts
    app.register_blueprint(accounts.bp)

    from . import transactions
    app.register_blueprint(transactions.bp)

    from . import transferences
    app.register_blueprint(transferences.bp)

    return app