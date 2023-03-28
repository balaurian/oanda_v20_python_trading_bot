import argparse
from .common import config

class API_V20():
    def __init__(self):
        self.api = None
        self.parser = argparse.ArgumentParser()
        config.add_argument(self.parser)
        
        self.args = self.parser.parse_args()
        
        self.account_id = self.args.config.active_account
        #
        # The v20 config object creates the v20.Context for us based on the
        # contents of the config file.
        #
        self.api = self.args.config.create_context() #returns ctx, <v20.Context object at 0x000002BA66A65908>
      
