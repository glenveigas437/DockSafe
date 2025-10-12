from flask import Blueprint

bp = Blueprint("groups", __name__)

from app.groups import routes
