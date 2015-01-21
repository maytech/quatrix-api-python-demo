#!/usr/bin/env python
# encoding: utf-8

import time
import urlparse
import argparse

import requests

from services.api import MaytechAPI
from services.api import MaytechAuth
from errors import RequestError
from errors import AuthorizationError


def make_temp_dir(root_id, api):
    folder = api.post('file/makedir',
                      {'name': 'test_tmp_%s' % time.time(), 'target': root_id})
    return folder['id']


def file_metadata(id, api):
    f = api.get('file/metadata/%s' % id)
    return f['content']


def get_upload_link(dir_id, name, api, upload_type='multipart'):
    url = api.post('upload/getlink',
                   {'name': name,
                    'parent': dir_id,
                    'upload_type': upload_type})
    return url


def upload_multipart(f, dir_id, api):
    link = get_upload_link(dir_id, f.name, api, 'multipart')
    url = urlparse.urljoin(api.referer, link)

    res = requests.post(url, files={"file": f}, verify=False)
    return res.elapsed


def main():
    parser = argparse.ArgumentParser(description='Quatrix API demo')
    parser.add_argument("--host", dest='host',
                        required=True,
                        help="Quatrix account host")

    parser.add_argument("-l", "--login", dest="login",
                        required=True,
                        help="User login")

    parser.add_argument("-p", "--password", dest="password",
                        required=True,
                        help="User password")

    args = vars(parser.parse_args())
    url = urlparse.urlparse(args['host'])
    base_url = urlparse.urlunparse((url.scheme or 'https',
                                    url.netloc or url.path,
                                    '/', '', '', ''))
    quatrix_api = base_url + 'api/0.1/'

    try:
        api = MaytechAPI(base_url, quatrix_api, auth=MaytechAuth)
        api.authorize({'username': args['login'],
                       'password': args['password']})
        profile = api.services['profile'].get()
        root_id = profile['rootId']
        print "Profile data:"
        print "-" * 30
        print "Name: %s" % profile['realname']
        print "Email: %s" % profile['email']
        print "\n"

        # List root cotents
        root_files = file_metadata(root_id, api)
        print "Root folder contents:"
        print "-" * 30
        for f in root_files:
            print "%s \"%s\"" % ("File" if f['type'] == "F" else "Folder", f['name'])
        print "\n"

        # Upload this file to API
        print "Uploading this file (%s) to API" % __file__
        with open(__file__) as f:
            upload_multipart(f, root_id, api)
        print "Finished upload"

    except AuthorizationError as e:
        print("Authorization error, please check user and password")
    except RequestError as e:
        print("Method %s failed with [%d] status code. Returned:\n%s" %
            (e.resource, e.status_code, e.response_text))


if __name__ == '__main__':
    main()
