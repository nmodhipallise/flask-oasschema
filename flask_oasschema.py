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


class _OASSchema(object):
    def __init__(self, schemas):
        self._schemas = schemas

    def get_schema(self, schema_file, uri_path, method):
        for parameter in self._schemas[schema_file]['paths'][uri_path][method]["parameters"]:
            if parameter.get('in', '') == 'body':
                parameter['schema']['definitions'] = self._schemas[schema_file]['definitions']
                return parameter['schema']
        raise ValidationError("Matching schema not found")


class OASSchema(object):
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self._state = self.init_app(app)

    def init_app(self, app):
        default_dir = os.path.join(app.root_path, 'jsonschema')
        schema_dir = app.config.get('JSONSCHEMA_DIR', default_dir)
        schemas = {}
        for fn in os.listdir(schema_dir):
            key = fn.split('.')[0]
            fn = os.path.join(schema_dir, fn)
            if os.path.isdir(fn) or not fn.endswith('.json'):
                continue
            with open(fn) as f:
                schemas[key] = json.load(f)
        state = _OASSchema(schemas)
        app.extensions['jsonschema'] = state
        return state

    def __getattr__(self, name):
        return getattr(self._state, name, None)


def validate_request(*path):
    """
    Validate request body's JSON against JSON schema in OpenAPI Specification

    Args:
        json_file (string): file name of the OAS json file, without .json suffix
        path      (string): OAS style application path http://goo.gl/2FHaAw
        method    (string): OAS style method (get/post..) http://goo.gl/P7LNCE

    Example:
        @app.route('/foo/<param>/bar', methods=['POST'])
        @validate_request_oas('oas', '/foo/{param}/bar', "post")
        def foo(param):
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            schema = current_app.extensions['jsonschema'].get_schema(*path)
            validate(request.get_json(), schema)
            return fn(*args, **kwargs)
        return decorated
    return wrapper
