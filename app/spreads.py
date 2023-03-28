#!/usr/bin/env python

import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

from app.api import API_V20
from app.events import SpreadEvent

class Spreads():
    def __init__(self):
        self.latest_price_time = None
        
        self.api =API_V20()
        self.account_id = self.api.account_id
        
        self.spreads_dict = {}

        self.raw_instruments = None

        self.top_instruments_to_str = ''
        self.top_instruments_to_list = []
        
        self.spreads_dataframe = None
        
        self.top_df = None
        self.top_instruments = None
        
        self.all_instruments_list = self.get_all_instruments()
        
        self.all_instruments_str =','.join(self.all_instruments_list)

        self.response = self.api.api.pricing.get(
            self.account_id,
            instruments=self.all_instruments_str.upper(),
            since=self.latest_price_time,
            includeUnitsAvailable=False)
        
        self.set_spread_dataframe()
        
    def set_spread_dataframe(self):
        for price in self.response.get("prices", 200):
            time, symbol, bid, ask = price.time, price.instrument, price.bids[0].price, price.asks[0].price
            spread = ask - bid
            self.spreads_dict[symbol] = spread, time#, spread/pip_location, pip_location, pip_location
        
        self.spreads_dataframe = pd.DataFrame.from_dict(self.spreads_dict, columns=['spread', 'time'],orient = 'index')
        #self.spreads_dataframe.dropna()
        self.spreads_dataframe = self.spreads_dataframe.sort_values(by='spread')
            
    def get_all_instruments(self):
        try:
            self.response_instruments = self.api.api.account.instruments(self.account_id)
        
        except:
            self.response_instruments = self.api.api.account.instruments(self.account_id)

        raw_instruments=[]
        
        try:
            self.instruments = self.response_instruments.get("instruments", "200")
        
        except:
            self.instruments = self.response_instruments.get("instruments", "200")
        
        for instrument in self.instruments:
            if instrument.type == 'CURRENCY':
                if instrument.name not in raw_instruments:
                    raw_instruments.append(instrument.name)
                    #margin_rate.append(instrument.marginRate)
        
        return raw_instruments
    
    def select_instruments(self, instruments_number, trades_list): #trades list is the list of existing opened trades
        spreads = []
        sel = self.spreads_dataframe.head(instruments_number)
        
        if trades_list:
            for x in range(0,len(trades_list)):
              if trades_list[x] in self.spreads_dataframe.index:
                if trades_list[x] not in sel.index:
                    pos=self.spreads_dataframe.index.get_loc(trades_list[x])
                    sel.loc[trades_list[x]]=self.spreads_dataframe.iloc[pos]

        for i in range(0,len(sel)):
            spread_object = SpreadEvent(\
                instrument = sel.index[i],
                spread = '{:6f}'.format(sel.iloc[i][0]),
                time = sel.iloc[i][1])
            spreads.append(spread_object)
        
        return spreads
