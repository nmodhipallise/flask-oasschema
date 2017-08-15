import os
import unittest

import simplejson as json

from flask import Flask
from flask_oasschema import OASSchema, validate_request, ValidationError

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['OAS_FILE'] = os.path.join(app.root_path, 'schemas', 'oas.json')
jsonschema = OASSchema(app)


@app.route('/books/<isbn>', methods=['POST'])
@validate_request()
def books_post(isbn):
    return 'success'


@app.route('/books/<isbn>', methods=['GET'])
@validate_request()
def books_get(isbn):
    return 'success'


@app.errorhandler(ValidationError)
def on_error(e):
    return 'error'

client = app.test_client()


class JsonSchemaTests(unittest.TestCase):

    def test_valid_json_post(self):
        r = client.post(
            '/books/0-330-25864-8',
            content_type='application/json',
            data=json.dumps({
                'title': 'The Hitchhiker\'s Guide to the Galaxy',
                'author': 'Douglas  Adams'
            })
        )
        self.assertIn(b'success', r.data)

    def test_invalid_json_post(self):
        r = client.post(
            '/books/0-316-92004-5',
            content_type='application/json',
            data=json.dumps({
                'title': 'Infinite Jest'
            })
        )
        self.assertIn(b'error', r.data)

    def test_valid_json_get(self):
        r = client.get(
            '/books/0-330-25864-8',
            query_string={
                'author': 'Douglas  Adams'
            }
        )
        self.assertIn(b'success', r.data)

    def test_invalid_json_get(self):
        r = client.get(
            '/books/0-330-25864-8',
            query_string={
                'author': 1234
            }
        )
        self.assertIn(b'error', r.data)
