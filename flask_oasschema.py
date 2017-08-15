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
import urllib


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


def extract_body_schema(schema, uri_path, method):

    prefix = schema.get("basePath")
    if prefix and uri_path.startswith(prefix):
        uri_path = uri_path[len(prefix):]
    for parameter in schema['paths'][uri_path][method]["parameters"]:
        if parameter.get('in', '') == 'body':
            parameter['schema']['definitions'] = schema['definitions']
            return parameter['schema']

    raise ValidationError("Matching schema not found")


def extract_query_schema(parameters):

    def schema_property(parameter_definition):
        schema_keys = ['type', 'format', 'enum']
        return {
            key: parameter_definition[key]
            for key in parameter_definition if key in schema_keys
        }

    schema = {
        'type': 'object',
        'properties': {
            parameter['name']: schema_property(parameter)
            for parameter in parameters if parameter.get('in', '') == 'query'
        },
        'required': [
            parameter['name']
            for parameter in parameters if parameter.get('required', False)
        ]
    }

    if len(schema['required']) == 0:
        del schema['required']

    return schema


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
        def convert_type(string_value):
            str_value = string_value.decode('utf8')
            try:
                return int(string_value)
            except ValueError:
                return str_value

        @wraps(fn)
        def decorated(*args, **kwargs):
            uri_path = request.url_rule.rule.replace("<", "{").replace(">", "}")
            method = request.method.lower()
            schema = current_app.extensions['oas_schema']

            if method == 'get':
                query = dict(urllib.parse.parse_qsl(request.query_string))
                query = {
                    key.decode('utf8'): convert_type(query[key])
                    for key in query
                }

                request_parameters = schema['paths'][uri_path][method].get("parameters")
                if request_parameters:
                    query_schema = extract_query_schema(request_parameters)
                    validate(query, query_schema)
            else:
                validate(request.get_json(), extract_body_schema(schema, uri_path, method))

            return fn(*args, **kwargs)
        return decorated
    return wrapper
