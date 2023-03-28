#from app.api import API_V20
from app.events import OrderEvent

from app.settings import *

class MoneyManager(object):
    def __init__(self):
        self.currency = None
        self.balance = None
        self.equity = None
        self.margin_used = None
        self.margin_available = None
        
        self.max_percent_total = max_percent_total
        self.max_percent_per_trade = max_percent_per_trade
        self.hedge_ratio = hedge_ratio
        self.pip_tp = pip_tp
        self.pip_sl = pip_sl
        
        self.tick_event = None
        
        self.signal_granularities = []
    
    def orders_pair_setup(self, event):
        orders_pair =[]
        instrument_data = event.instrument_data
        portfolio_data = event.portfolio
        self.total_allowed = portfolio_data.equity*self.max_percent_total
        self.trade_allowed = self.total_allowed*self.max_percent_per_trade

        order_pip_values,main_trade_units,secondary_trade_units = self.order_details_setup(instrument_data)

        position_units  = [main_trade_units,-secondary_trade_units] if event.direction == True  else [-main_trade_units,secondary_trade_units]
        
        for units in position_units:
            order = OrderEvent()
            order.instrument = event.instrument
            order.time = event.time
            order.trade_pip_value = order_pip_values[0] if units > 0 else order_pip_values[1]
            order.margin = instrument_data.margins[0]*abs(units)/instrument_data.contract_size  if units > 0 else instrument_data.margins[1]*abs(units)/instrument_data.contract_size
            
            order.tp = self.pip_tp #if units == position_units[0] else None
            order.sl = self.pip_sl #if units == position_units[1] else None
            
            order.units = units

            order.ok = True

            order.expected_profit = self.pip_tp*order.trade_pip_value if units == position_units[0] else self.pip_tp*order.trade_pip_value/self.hedge_ratio
            order.expected_loss = self.pip_sl*order.trade_pip_value if units == position_units[0] else self.pip_sl*order.trade_pip_value/self.hedge_ratio

            order.trade_pip_value = round(order.trade_pip_value,3)
            order.margin = round(order.margin,3)
            order.expected_profit = round(order.expected_profit,3)
            order.expected_loss = round(order.expected_loss,3)
            
            #self.events_queue.put(order)
            orders_pair.append(order)
        
        return orders_pair

    def order_details_setup(self, instrument_data):
        order_pip_values = [instrument_data.pip_values[0]*self.trade_allowed/instrument_data.margins[0],instrument_data.pip_values[1]*self.trade_allowed/instrument_data.margins[1]]
        #units available to trade with self.trade_allowed
        units = instrument_data.contract_size * self.trade_allowed/instrument_data.margins[0]
        
        main_trade_units = int(units)
        secondary_trade_units = int(main_trade_units/self.hedge_ratio)

        return order_pip_values,main_trade_units,secondary_trade_units