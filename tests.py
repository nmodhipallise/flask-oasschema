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
def books(isbn):
    return 'success'


@app.route('/health', methods=['GET'])
@validate_request()
def health():
    return 'success'


@app.errorhandler(ValidationError)
def on_error(e):
    return 'error'

client = app.test_client()


class JsonSchemaTests(unittest.TestCase):

    def test_valid_json(self):
        r = client.post(
            '/books/0-330-25864-8',
            content_type='application/json',
            data=json.dumps({
                'title': 'The Hitchhiker\'s Guide to the Galaxy',
                'author': 'Douglas  Adams'
            })
        )
        self.assertIn('success', r.data)

    def test_invalid_json(self):
        r = client.post(
            '/books/0-316-92004-5',
            content_type='application/json',
            data=json.dumps({
                'title': 'Infinite Jest'
            })
        )
        self.assertIn('error', r.data)

    def test_no_params(self):
        """
        No parameters are defined in schema so there is nothing to check.
        Either schema should be defined or decorator shouldn't be used on endpoint
        """
        r = client.get('/health')
        self.assertIn('error', r.data)
