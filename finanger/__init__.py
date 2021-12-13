import os

from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'finanger.sqlite'),
    )

    app.config.from_pyfile('config.py', silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    

    from .utils import brl, day_name_number, month_name
    app.jinja_env.filters["brl"] = brl
    app.jinja_env.filters["day_name_number"] = day_name_number
    app.jinja_env.filters["month_name"] = month_name

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

    from . import transfers
    app.register_blueprint(transfers.bp)

    return app