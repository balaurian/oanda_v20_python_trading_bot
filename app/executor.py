import time

from app.api import API_V20
from app.settings import api_connect

class Executor(object):
    def __init__(self):
        self.api =API_V20()
        self.account_id = self.api.account_id
        self.events_queue = None
        self.kwargs = {}
        
    def market(self, event):
        self.kwargs['instrument'] = event.instrument
        self.kwargs['units'] = event.units
        
        def connection():
            return self.api.api.order.market(self.account_id, **self.kwargs)
        
        try:
            response = connection()

        except:
            time.sleep(api_connect)
            try:
                response = connection()

            except:
                time.sleep(api_connect)
                response = connection()
        
        return response

    def open_trade(self, instrument,units):
        self.kwargs['instrument'] = instrument
        self.kwargs['units'] = units
        try:
            response = self.api.api.order.market(self.account_id, **self.kwargs)
        
        except:
            response = self.api.api.order.market(self.account_id, **self.kwargs)

        return response
    
    def close_trade(self,id,units):
        response = self.api.api.trade.close(
        self.account_id,
        id,
        units=units
        )
        return response
        
    def close_position(self, instrument,long_units=None, short_units=None):
        if long_units is not None and short_units is not None:
            response = self.api.api.position.close(
                self.account_id,
                instrument=instrument,
                longUnits=long_units,
                shortUnits=short_units
            )

        elif long_units is not None:
            response = self.api.api.position.close(
                self.account_id,
                instrument=instrument,
                longUnits=long_units
            )

        elif short_units is not None:
            response = self.api.api.position.close(
                self.account_id,
                instrument=instrument,
                shortUnits=short_units
            )
        return response            