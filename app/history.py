#https://stackoverflow.com/questions/474528/what-is-the-best-way-to-repeatedly-execute-a-function-every-x-seconds/25251804#25251804
import os
from datetime import datetime
import time
import pandas as pd

from app.api import API_V20
from app.events import HistoryEvent

from app.settings import *


#from spreads import Spreads

#pentru plotter.py
import matplotlib.pyplot as plt
import numpy as np

class History():
    def __init__(self):
        self.api=API_V20()
        self.account_id = self.api.account_id

        self.path = '/app/data/history'
        
        self.historic = HistoryEvent()
        #calculates spreas and picks self.top_size pairs
        # self.top_size = 2
        # self.spreads = Spreads()
        # self.spreads.get_top_instruments(self.top_size)
        
        # self.instruments = self.spreads.top_instruments_to_list
        
        # self.history_dict = {}

        # self.starttime= time.time()

        # self.count = 10
        # self.kwargs = {}
        # self.kwargs['count'] = self.count
        #self.granularities = ['H1', 'M']
    
    def update_history(self,instrument,granularity,count):
        dataframe=self.get_instrument_candles(instrument,granularity = granularity, count = count, write_csv=True)

    def get_all_instruments_candles(self, instruments):
        for instrument in instruments:
            for granularity in self.granularities:
                self.get_instrument_candles(instrument, granularity, self.count)# = dataframe
                #self.history_to_csv(instrument, dataframe, granularity)
    
    def get_candles_by_timeframe(self, instruments, granularity, count):
        for instrument in instruments:
            self.get_instrument_candles(instrument, granularity, count)

    def get_instrument_candles(self, instrument, granularity, count, write_csv=True):
        self.kwargs['granularity'] = granularity
        self.kwargs['count'] = count
        def connection(instrument):
            return self.api.instrument.candles(instrument=instrument, **self.kwargs)
        
        try:
            response = connection(instrument)

        except:
            time.sleep(api_connect)
            try:
                response = connection(instrument)
            except:
                time.sleep(api_connect)
                response = connection(instrument)

        candles = response.get('candles', 200)
        
        columns = ['time', 'type', 'open', 'high', 'low', 'close', 'volume']
        
        data =[]
        
        for candle in candles:
            data.append(self.unfold_candle(candle))
    
        dataframe = pd.DataFrame(data, columns= columns)
        dataframe.index = dataframe['time']
        del dataframe['time']
        
        print('updating history {} {} ... '.format(response.get('instrument', 200), response.get('granularity', 200)))
        #print('granularity: {}'.format(response.get('granularity', 200)))
        #print (dataframe)

        if write_csv == True:
            self.dataframe_to_csv(instrument, granularity, dataframe)

        return dataframe
    
    def unfold_candle(self, candle):
        try:
            time = str(
                datetime.strptime(
                    candle.time,
                    '%Y-%m-%dT%H:%M:%S.000000000Z'
                )
            )
        except:
            time = candle.time.split('.')[0]

        volume = candle.volume

        for price in ['mid', 'bid', 'ask']:
            c = getattr(candle, price, None)
            if c is None:
                continue
            
            time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
            
            return time, price, c.o, c.h, c.l, c.c, volume
    
    def dataframe_to_csv(self, instrument, granularity, dataframe, backup=True):
        intrument_folder = f'{self.path}/{instrument}'
        instrument_file_name =f'{instrument}_{granularity}.csv'
        instrument_file_path =f'{intrument_folder}/{instrument}_{granularity}.csv'
        
        if not os.path.exists(intrument_folder):
            os.mkdir(intrument_folder)
        
        if instrument_file_name not in os.listdir(intrument_folder):
            dataframe.to_csv(instrument_file_path)
        
        elif backup:
            existing_data = pd.read_csv(instrument_file_path,header=0, index_col=0, parse_dates=True, squeeze=True)
            for i in dataframe.index:
                if i not in existing_data.index:
                    existing_data.loc[i] = dataframe.loc[i]
            
            existing_data.to_csv(instrument_file_path)
        
        else:
            dataframe.to_csv(instrument_file_path)