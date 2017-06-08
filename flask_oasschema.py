# -*- coding: utf-8 -*-
"""
    flask_oasschema
    ~~~~~~~~~~~~~~~~

    flask_oasschema
"""

import os

from functools import wraps

try:
    import simplejson as json
except ImportError:
    import json

from flask import current_app, request
from jsonschema import ValidationError, validate


class OASSchema(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self._state = self.init_app(app)

    def init_app(self, app):
        default_file = os.path.join(app.root_path, 'schemas', 'oas.json')
        schema_path = app.config.get('OAS_FILE', default_file)
        with open(schema_path, 'r') as schema_file:
            schema = json.load(schema_file)
        app.extensions['oas_schema'] = schema
        return schema

    def __getattr__(self, name):
        return getattr(self._state, name, None)


def extract_schema(schema, uri_path, method):
    prefix = schema.get("basePath")
    if prefix and uri_path.startswith(prefix):
        uri_path = uri_path[len(prefix):]
    for parameter in schema['paths'][uri_path][method]["parameters"]:
        if parameter.get('in', '') == 'body':
            parameter['schema']['definitions'] = schema['definitions']
            return parameter['schema']
    raise ValidationError("Matching schema not found")


def validate_request():
    """
    Validate request body's JSON against JSON schema in OpenAPI Specification

    Args:
        path      (string): OAS style application path http://goo.gl/2FHaAw
        method    (string): OAS style method (get/post..) http://goo.gl/P7LNCE

    Example:
        @app.route('/foo/<param>/bar', methods=['POST'])
        @validate_request()
        def foo(param):
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            uri_path = request.url_rule.rule.replace("<", "{").replace(">", "}")
            method = request.method.lower()
            schema = current_app.extensions['oas_schema']
            validate(request.get_json(), extract_schema(schema, uri_path, method))
            return fn(*args, **kwargs)
        return decorated
    return wrapper
