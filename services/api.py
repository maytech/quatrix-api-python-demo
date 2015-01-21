import time
import requests
import urllib2
import json
from urlparse import urlparse
import hmac
from hashlib import sha1
from requests.auth import AuthBase

from profile import Profile
from errors import RequestError
from errors import AuthorizationError

from passlib.utils.pbkdf2 import pbkdf2


class MaytechAuth(AuthBase):
    def __init__(self, referer, url, data, verify=False):
        self.username = data['username']
        self.password = pbkdf2(data['password'], "", 4096, 32).encode('hex')
        self.verify = verify

        login_url = url + 'session/login'
        timestamp = int(time.time())
        login_text = 'GET %s\nx-auth-login: %s\nx-auth-timestamp: %s\n' % \
            ('/session/login', self.username, timestamp)
        login_authorization = hmac.new(self.password, login_text, sha1).hexdigest()

        login_headers = {
            'authorization': login_authorization,
            'X-Auth-Login': self.username,
            'X-Auth-Timestamp': str(timestamp),
            'Referer': referer
        }

        r = requests.get(login_url, headers=login_headers, verify=self.verify)
        if r.status_code == 200:
            self.auth_token = r.headers['x-auth-token']
        else:
            raise AuthorizationError

    def __call__(self, request):
        timestamp = int(time.time())
        url = urllib2.unquote(urlparse(request.url).path)
        # removing
        if url.startswith(MaytechAPI.API_PREFIX):
            url = url[len(MaytechAPI.API_PREFIX):]

        text = '%s %s\nx-auth-timestamp: %s\nx-auth-token: %s\n' %\
            (request.method, url, timestamp, self.auth_token)

        request.headers['X-Auth-Timestamp'] = timestamp
        request.headers['X-Auth-Token'] = self.auth_token
        request.headers['authorization'] = hmac.new(self.password, text, sha1).hexdigest()

        return request


class MaytechAPI(object):

    REQUEST_HEADER = {'content-type': 'application/json'}
    API_PREFIX = '/api/0.1'

    def __init__(self, referer, url, verify=False, **kwargs):
        self.verify = verify
        self.url = url
        self.referer = referer
        self.user_name = kwargs.get('user_name', None)
        self.password = kwargs.get('password', None)
        self.auth = kwargs['auth']
        self.services = {
            'profile': Profile(self),
        }

    def authorize(self, data):
        self.auth = self.auth(self.referer, self.url, data)

    def get(self, resource):
        headers = MaytechAPI.REQUEST_HEADER
        url = self.url + resource
        request = requests.get(url, headers=headers, auth=self.auth, verify=self.verify)
        if request.status_code == 200:
            return json.loads(request.text)
        else:
            raise RequestError('GET ' + url, request.status_code, request.text)

    def post(self, resource, data):
        headers = MaytechAPI.REQUEST_HEADER
        url = self.url + resource
        response = requests.post(url, data=json.dumps(data), headers=headers, auth=self.auth, verify=self.verify)
        if response.status_code < 300:
            return json.loads(response.text)
        else:
            raise RequestError('POST ' + url, response.status_code, response.text)
