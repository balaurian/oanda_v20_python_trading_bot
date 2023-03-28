import time

from app.api import API_V20
from app.events import InstrumentEvent
from app.common.common_func import get_date

from app.settings import *

class InstrumentData():
    def __init__(self):
        self.api=API_V20()
        self.account_id = self.api.account_id
        
        self.account_currency = account_currency
        self.all=[]
        self.spread = None
        self.units = 10000
        self.contract_size = None
        self.commission = 1
        self.instruments = []
        
        ##granularities##
        self.M1 = 'M1'
        self.M5 = 'M5'
        self.M15 = 'M15'
        self.M30 = 'M30'
        self.H1 = 'H1'
        self.H4 = 'H4'
        self.D = 'D'
        self.W = 'W'
        self.M = 'M'
        
    
    def pip_format(self, instrument):
        location = float(10 ** instrument.pipLocation)
        return float('{:.6f}'.format (location))

    def margin_format(self,instrument):
        return '{:.3f}'.format(float(instrument.marginRate)) #Leverage = 1/Margin = 100/Margin Percentage
    
    def required_margin(self,price, pip, margin_rate, contract_size):
        margin = price*self.units*float(pip)*contract_size*float(margin_rate)
        
        return float('{:.5f}'.format(margin))
    
    def currency_convert(self, instrument_name):
        def connection(instrument_name):
            #https://www.xm.com/forex-calculators/margin
            convertion_rate_response = self.api.api.pricing.get(
                                    self.account_id,
                                    instruments=instrument_name,
                                    includeUnitsAvailable=False)
            
            for rate in convertion_rate_response.get("prices", 200):
                bid, ask = rate.bids[0].price, rate.asks[0].price
                
            return  ask,bid
        
        try:
            ask,bid = connection(instrument_name)

        except:
            time.sleep(api_connect)
            try:
                ask,bid = connection(instrument_name)
            
            except:
                time.sleep(api_connect)
                ask,bid = connection(instrument_name)
        
        return ask,bid

    def instrument_setup(self, instrument):#, spread, time):
        def connection(instrument):
            return self.api.api.pricing.get(
                self.account_id,
                instruments=instrument,
                includeUnitsAvailable=False)
        try:
            price_response = connection(instrument)

        except :
            time.sleep(api_connect)
            try:
                price_response = connection(instrument)

            except:
                time.sleep(api_connect)
                price_response = connection(instrument)
        
        all_instruments_response = self.api.api.account.instruments(
            self.account_id)
        
        self.all_instruments = all_instruments_response.get("instruments", "200")
        
        for item in self.all_instruments:
            if item.name not in self.all:
                self.all.append(item.name)

        instrument_object = None
        
        for price in price_response.get("prices", 200):
            symbol, bid, ask = price.instrument, price.bids[0].price, price.asks[0].price
            multiply=False
            spread = ask - bid
            time = get_date()
            for i in self.all_instruments:
                if symbol == i.name:
                    instrument_name = i.name
                    
                    contract_size = 10**abs(i.pipLocation)

                    ask_pip = self.pip_format(i)
                    bid_pip = self.pip_format(i)
                    
                    margin_rate = self.margin_format(i)
                    
                    ask_margin = self.required_margin(ask,ask_pip,margin_rate, contract_size)
                    bid_margin = self.required_margin(bid,bid_pip,margin_rate, contract_size)
                    
                    pip_values = [ask_pip*contract_size, bid_pip*contract_size]
                    
                    if instrument_name[-3:] != self.account_currency:#if base_currency nu e USD, atunci calculez rata de schimb a base_currency/USD
                        last_three = instrument_name[-3:]
                        instrument_to_convert = f'{last_three}_{self.account_currency}'
                        
                        if instrument_to_convert in self.all:
                            multiply = True#AUD/USD
                        else:
                            instrument_to_convert=f'{instrument_to_convert[-3:]}_{instrument_to_convert[:3]}'
                            
                        # for raw_instrument in self.instruments:
                        #     if instrument_to_convert in raw_instrument: 
                        #         multiply = True#AUD/USD
                            
                        #     elif instrument_name[-3:] in raw_instrument and self.account_currency in raw_instrument:
                        #         instrument_to_convert = raw_instrument#USD/CHF
                        #         multiply = False
                        
                        ask_price, bid_price = self.currency_convert(instrument_to_convert)
                        
                        if multiply:
                            ask_pip = ask_pip*ask_price
                            bid_pip = bid_pip*bid_price
                            
                            ask_margin = ask_margin*ask_price
                            bid_margin = bid_margin*bid_price
                        
                        else:
                            ask_pip = ask_pip/ask_price
                            bid_pip = bid_pip/bid_price
                            
                            ask_margin = ask_margin/ask_price
                            bid_margin = bid_margin/bid_price

                        pip_values = [ask_pip*contract_size, bid_pip*contract_size]
                
                    instrument_object = InstrumentEvent(\
                        instrument=instrument_name, \
                        ask=ask,\
                        bid=bid,\
                        time = time,\
                        spread = float(spread)*contract_size, \
                        pip_location = i.pipLocation,\
                        pip_values = pip_values, \
                        margins = [ask_margin, bid_margin], \
                        contract_size = contract_size,\
                        margin_rate = margin_rate) 
        
        return instrument_object

    def setup(self, spreads): #spreads --> [spread_event.instrument, spread_event.spread]
        instrument_objects = [] 
        
        for i in range(0,len(spreads)):
            self.instruments.append(spreads[i].instrument)
            
            instrument_objects.append(self.instrument_setup(spreads[i].instrument, spreads[i].spread, spreads[i].time))
            
            #if instrument_object:
            # for granularity in [self.M1,self.M5,self.M15,self.M30,self.H1,self.H4,self.D,self.W,self.M]:
            #     df = hist_data.candles_by_instrument(spreads[i].instrument, granularity = granularity, count = 200, write_csv=True)
                
            #     if granularity == self.M1:
            #         instrument_object.set_M1(df)
                
            #     elif granularity == self.M5:
            #         instrument_object.set_M5(df)
                
            #     elif granularity == self.M15:
            #         instrument_object.set_M15(df)
                
            #     elif granularity == self.M30:
            #         instrument_object.set_M30(df)
                
            #     elif granularity == self.H1:
            #         instrument_object.set_H1(df)
                
            #     elif granularity == self.H4:
            #         instrument_object.set_H4(df)
                
            #     elif granularity == self.D:
            #         instrument_object.set_D(df)
                
            #     elif granularity == self.W:
            #         instrument_object.set_W(df)
                
            #     elif granularity == self.M:
            #         instrument_object.set_M(df)
                
            #     if instrument_object not in instrument_objects:
            #         instrument_objects.append(instrument_object)

            #else:
            #    print ('plm', spreads[i].instrument, spreads[i].spread, instrument_object)

        return instrument_objects
