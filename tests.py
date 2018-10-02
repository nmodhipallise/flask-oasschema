import os
import unittest

import simplejson as json

from flask import Flask
from flask_oasschema import OASSchema, validate_request, ValidationError

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['OAS_FILE'] = os.path.join(app.root_path, 'schemas', 'oas.json')
jsonschema = OASSchema(app)


@app.route('/books/<isbn>', methods=['PUT'])
@validate_request()
def books_post(isbn):
    return 'success'


@app.route('/books/by-author', methods=['GET'])
@validate_request()
def books_get_author():
    return 'success'


@app.route('/books/by-author-in-body', methods=['GET'])
@validate_request()
def books_get_author_in_body():
    return 'success'


@app.route('/books/by-title', methods=['GET'])
@validate_request()
def books_get_title():
    return 'success'


@app.errorhandler(ValidationError)
def on_error(e):
    return 'error'

client = app.test_client()


class JsonSchemaTests(unittest.TestCase):

    def test_valid_json_put(self):
        r = client.put(
            '/books/0-330-25864-8',
            content_type='application/json',
            data=json.dumps({
                'title': 'The Hitchhiker\'s Guide to the Galaxy',
                'author': 'Douglas  Adams'
            })
        )
        self.assertIn(b'success', r.data)

    def test_invalid_json_put(self):
        r = client.put(
            '/books/0-316-92004-5',
            content_type='application/json',
            data=json.dumps({
                'title': 'Infinite Jest'
            })
        )
        self.assertIn(b'error', r.data)

    def test_valid_get(self):
        r = client.get(
            '/books/by-title',
            query_string={
                'title': 'The Hitchhiker\'s Guide to the Galaxy'
            }
        )
        self.assertIn(b'success', r.data)

    def test_valid_get_numeric_string(self):
        r = client.get(
            '/books/by-title',
            query_string={
                'title': '1234'
            }
        )
        self.assertIn(b'success', r.data)

    def test_no_param_get(self):
        r = client.get(
            '/books/by-author'
        )
        self.assertIn(b'success', r.data)

    def test_valid_json_get(self):
        r = client.get(
            '/books/by-author-in-body',
            content_type='application/json',
            data=json.dumps({
                'author': 'Douglas  Adams'
            })
        )
        self.assertIn(b'success', r.data)

