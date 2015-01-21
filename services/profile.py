class Profile(object):
    def __init__(self, api):
        self.resource = 'profile/'
        self.api = api

    def get(self):
        return self.api.get(self.resource + 'get')