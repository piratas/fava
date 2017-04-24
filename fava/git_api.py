"""GIT API."""

import hashlib
import hmac
import os
import re
import random

from flask import Blueprint, jsonify, json, g, request

from fava import util
from fava.core.helpers import FavaAPIException


KEY = u'test'.encode('utf-8')
git_api = Blueprint('git_api', __name__)  # pylint: disable=invalid-name


@git_api.errorhandler(FavaAPIException)
def _git_api_exception(error):
    return jsonify({'success': False, 'error': message})


@git_api.route('/webhook', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    header = request.headers.get('X-Hub-Signature')

    if not header:
        raise FavaAPIException('Missing signature header.')

    algorithm, signature = header.split('=')
    if algorithm not in hashlib.algorithms_available:
        raise FavaAPIException('Invalid hash algorithm.')

    digest = hmac.new(KEY, request.data, getattr(hashlib,algorithm)).hexdigest()
    if not hmac.compare_digest(signature, digest):
        raise FavaAPIException('Invalid signature.')

    payload = json.loads(request.data)
    if 'push' == event:
        return jsonify({'success': True, 'changed': g.ledger.changed()})
    elif 'ping' == event:
        zen = re.sub('[=,.!?]', '', payload['zen']).lower().split()
        random.shuffle(zen)
        return jsonify({'success': True, 'changed': False,
            'zen' : ' '.join([zen[0].capitalize()] + zen[1:]) + '!'})
    else:
        raise FavaAPIException('Unsuported event.')
