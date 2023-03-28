import time

from app.events import TickEvent
from app.api import API_V20

from app.settings import api_connect

class PriceStreamer():
    def __init__(self, instruments, queue):
        self.api_v20 = API_V20()
        self.api = self.api_v20.api
        self.account_id = self.api_v20.account_id
        
        self.latest_price_time = None
        self.instruments = instruments
        self.queue = queue
        self.tick_event = TickEvent()
    def price_response(self):
        def connection():
            return self.api.pricing.get(
                self.account_id,
                instruments=self.instruments,
                since=self.latest_price_time,
                includeUnitsAvailable=False)
        
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
    
    def ticks_handler(self):
        response = self.price_response()
        
        for price in response.get("prices", 200):
            if self.latest_price_time is None or price.time > self.latest_price_time:
                #print(price.closeoutBid)
                time, symbol, bid, ask = price.time, price.instrument, price.bids[0].price, price.asks[0].price
            
                tick_event = self.tick_event_init(time, symbol, bid, ask)
                #print ('tick from {} is set...\n'.format (symbol))

                self.queue.put((2,tick_event))
                #print ('{} sent to queue, {}...'.format(symbol, time))
        
        for price in response.get("prices", 200):
            if self.latest_price_time is None or price.time > self.latest_price_time:
                self.latest_price_time = price.time
        
        return self.latest_price_time
        
    def tick_event_init(self,time, symbol, bid, ask):
        
        self.tick_event.instrument = symbol
        self.tick_event.price = [ask, bid]
        self.tick_event.time = time
        
        return self.tick_event