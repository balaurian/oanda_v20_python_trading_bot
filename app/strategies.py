#!/usr/bin/env python
import numpy as np
import random
#import indicators
#import plotter
#from app.historical_data import HistoricalData

from app.events import SignalEvent
from app.instruments_setup import InstrumentData

class Strategy():
    def __init__(self):
        self.count = 200
        self.history = None#HistoricalData() 
        self.instruments = None#self.history.instruments
        self.indicators = None#indicators.indicators()
        self.plotter = None#plotter.plotter()
        self.events_queue = None
        self.tick_event = None
        self.direction = True
        
    def event_handler(self,event, events_queue): 
        self.events_queue = events_queue
        
        if event.type == 'tick_event':
            #tests a strategy on the newly ticked instrument
            self.hlhb_trend_catcher(event.instrument)
        
        if event.type == 'instrument_event':
            strategy='tbd'
            if self.direction:
                #direction=random.randint(0,1)
                self.direction = False
            else:
                self.direction = True
            
            granularity = 'tbd'
            signal=self.signal_event_setup(event,strategy,self.direction,granularity)

            self.events_queue.put((1,signal))
    
    def signal_event_setup(self, event,strategy, direction, granularity):
        signal_event = SignalEvent()
        signal_event.instrument = event.instrument
        #signal_event.price = event.price
        signal_event.time = event.time
        signal_event.strategy = strategy
        signal_event.direction = direction
        signal_event.granularity = granularity
        signal_event.instrument_data = event

        return signal_event

    def translate_granularities(self, instrument_object):
        dataframe_dict = {}
        dataframe_dict['M1'] = instrument_object.M1
        dataframe_dict['M5'] = instrument_object.M5
        dataframe_dict['M15'] = instrument_object.M15
        dataframe_dict['M30'] = instrument_object.M30
        dataframe_dict['H1'] = instrument_object.H1
        dataframe_dict['H4'] = instrument_object.H4
        dataframe_dict['D'] = instrument_object.D
        dataframe_dict['W'] = instrument_object.W
        dataframe_dict['M'] = instrument_object.M
        return dataframe_dict


    def hlhb_trend_catcher(self,instrument_object, fast = 5, slow = 10, rsi_period =10, count=200, ema=True):
        #https://www.babypips.com/trading/forex-ea-20150529
        #https://www.youtube.com/watch?v=rO_cqa4x60o
        #Algorithmic Trading Strategy Using Three Moving Averages & Python
        
        #buy when:
        #previous_fast < previous_slow
        #   && current_fast > current_slow 
        #previous_rsi < 50.0 && current_rsi > 50.0
        
        #sell when:
        #previous_fast > previous_slow 
        # && current_fast_ma < current_slow_ma
        #previous_rsi > 50.0 && current_rsi < 50.0
        
        dataframe_dict = {}
        dataframe_dict['M1'] = instrument_object.M1
        dataframe_dict['M5'] = instrument_object.M5
        dataframe_dict['M15'] = instrument_object.M15
        dataframe_dict['M30'] = instrument_object.M30
        dataframe_dict['H1'] = instrument_object.H1
        dataframe_dict['H4'] = instrument_object.H4
        dataframe_dict['D'] = instrument_object.D
        dataframe_dict['W'] = instrument_object.W
        dataframe_dict['M'] = instrument_object.M
        
        for gran in dataframe_dict.keys():
        
            if ema == False:
                fast_ma = self.indicators.sma(dataframe_dict[gran], fast)
                slow_ma = self.indicators.sma(dataframe_dict[gran], slow)
            else:
                fast_ma = self.indicators.ema(dataframe_dict[gran], fast)
                slow_ma = self.indicators.ema(dataframe_dict[gran], slow)
            
            rsi = self.indicators.rsi(dataframe_dict[gran], rsi_period)
            
            dataframe_dict[gran]['fast_ma'] = fast_ma
            dataframe_dict[gran]['slow_ma'] = slow_ma
            dataframe_dict[gran]['rsi'] = rsi
            
            dataframe = self.hlhb_logic(dataframe_dict[gran], gran)
            
            #plot the indicator
            #self.plotter.plot_sma_rsi(dataframe,instrument_object.instrument,count,
                #fast,slow,rsi_period)

    def hlhb_logic(self, dataframe, granularity):
        buy_list = []
        sell_list = []
        flag_long = False
        flag_short = False

        signal_event = None

        for i in range(0, len(dataframe)):
            if dataframe.fast_ma[i-1] < dataframe.slow_ma[i-1] and dataframe.fast_ma[i] > dataframe.slow_ma[i] and \
             dataframe.rsi[i-1] < 50.0 and dataframe.rsi[i] > 50.0 and \
             flag_long == False:
                buy_list.append(dataframe.close[i])
                sell_list.append(np.nan)
                flag_short = True
                signal_event = self.signal_event_setup(self.tick_event, 'hlhb_trend_catcher', 'buy', granularity)
                #print('buy @ {}, time is {} '.format(dataframe.close[i], dataframe.index[i]))

            elif flag_short == True and \
                dataframe.fast_ma[i-1] > dataframe.slow_ma[i-1] and dataframe.fast_ma[i] < dataframe.slow_ma[i] and \
                dataframe.rsi[i-1] > 50.0 and dataframe.rsi[i] < 50.0:
                sell_list.append(dataframe.close[i])
                buy_list.append(np.nan)
                flag_short = False
                signal_event = self.signal_event_setup(self.tick_event, 'hlhb_trend_catcher', 'sell', granularity)
                #print('sell @ {}, time is {} '.format(dataframe.close[i], dataframe.index[i]))

            elif dataframe.fast_ma[i-1] < dataframe.slow_ma[i-1] and dataframe.fast_ma[i] > dataframe.slow_ma[i] and \
             dataframe.rsi[i-1] < 50.0 and dataframe.rsi[i] > 50.0 and \
             flag_long == False:
                buy_list.append(dataframe.close[i])
                sell_list.append(np.nan)
                flag_long = True
                signal_event = self.signal_event_setup(self.tick_event, 'hlhb_trend_catcher', 'buy', granularity)
                #print('buy @ {}, time is {} '.format(dataframe.close[i], dataframe.index[i]))
            
            elif flag_long == True and \
                dataframe.fast_ma[i-1] > dataframe.slow_ma[i-1] and dataframe.fast_ma[i] < dataframe.slow_ma[i] and \
                dataframe.rsi[i-1] > 50.0 and dataframe.rsi[i] < 50.0:
                sell_list.append(dataframe.close[i])
                buy_list.append(np.nan)
                flag_long = False
                signal_event = self.signal_event_setup(self.tick_event, 'hlhb_trend_catcher', 'sell', granularity)
                #print('sell @ {}, time is {} '.format(dataframe.close[i], dataframe.index[i]))
            
            else:
                buy_list.append(np.nan)
                sell_list.append(np.nan)
        
        dataframe['buy'] = buy_list
        dataframe['sell'] = sell_list
        
        if signal_event:
            self.events_queue.put(signal_event)
            print ('\nsignal event sent from {} ...'.format(signal_event.granularity))
        return dataframe

    def sma_crossover_pullback(self):
        #https://www.babypips.com/trading/forex-system-20150605
        pass
    
    def ema_crossover(self):
        #https://forums.babypips.com/t/amazing-crossover-system-100-pips-per-day/19403
        pass

    def macd(self):
        #https://www.youtube.com/watch?v=kz_NJERCgm8
        pass
    
    def bollinger_bands(self):
        #https://www.youtube.com/watch?v=gEIw2iUlFYc
        pass