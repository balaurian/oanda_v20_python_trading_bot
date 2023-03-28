class event(object):
    pass

class TimeframeUpdateEvent(event): #triggered by threading.Timer
    def __init__(self,granularity=None):
        self.type = 'timeframeupdate_event'
        if granularity == 60:
            granularity = 'M1'
        
        elif granularity == 300:
            granularity = 'M5'
        
        if granularity == 900:
            granularity = 'M15'
        
        elif granularity == 1800:
            granularity = 'M30'

        if granularity == 3600:
            granularity = 'H1'
        
        elif granularity == 14400:
            granularity = 'H4'
        
        if granularity == 86400:
            granularity = 'D'
        
        elif granularity == 604800:
            granularity = 'W'
        
        if granularity == 2592000:
            granularity = 'M'
            
        self.granularity = granularity

class SpreadEvent(event):
    def __init__(self, instrument = None, spread = None, time = None):
        self.type = 'spread_event'
        self.instrument = instrument
        self.spread = spread
        self.time = time

class InstrumentEvent(event):
    def __init__(self, instrument=None,ask=None,bid=None,time=None,spread=None,pip_values=None,margins=None,contract_size=None,margin_rate=None,pip_location=None):
        self.type = 'instrument_event'
        self.instrument = instrument
        self.ask=ask
        self.bid=ask
        self.time = time
        self.spread = spread
        self.pip_values = pip_values
        self.margins = margins
        self.contract_size = contract_size
        self.margin_rate = margin_rate
        self.pip_location = pip_location
        self.last_update = None
        self.ok = False
        self.M1 = None
        self.M5 = None
        self.M15 = None
        self.M30 = None
        self.H1 = None
        self.H4 = None
        self.D = None
        self.W = None
        self.M = None
        
    def set_M1(self, M1_df):
        self.M1 = M1_df
        self.last_update = 'M1'
    
    def set_M5(self, M5_df):
        self.M5 = M5_df
        self.last_update = 'M5'
    
    def set_M15(self, M15_df):
        self.M15 = M15_df
        self.last_update = 'M15'
    
    def set_M30(self, M30_df):
        self.M30 = M30_df
        self.last_update = 'M30'
    
    def set_H1(self, H1_df):
        self.H1 = H1_df
        self.last_update = 'H1'
    
    def set_H4(self, H4_df):
        self.H4 = H4_df
        self.last_update = 'H4'
    
    def set_D(self, D_df):
        self.D = D_df
        self.last_update = 'D'
    
    def set_W(self, W_df):
        self.W = W_df
        self.last_update = 'W'
    
    def set_M(self, M_df):
        self.M = M_df
        self.last_update = 'M'

class HistoryEvent(event):
    def __init__(self, instrument=None,time=None,last_update=None):
        self.type = 'history_event'
        self.instrument = instrument
        self.time = time
        self.last_update = last_update
        self.M1 = None
        self.M5 = None
        self.M15 = None
        self.M30 = None
        self.H1 = None
        self.H4 = None
        self.D = None
        self.W = None
        self.M = None
        
    def set_M1(self, M1_df):
        self.M1 = M1_df
        self.last_update = 'M1'
    
    def set_M5(self, M5_df):
        self.M5 = M5_df
        self.last_update = 'M5'
    
    def set_M15(self, M15_df):
        self.M15 = M15_df
        self.last_update = 'M15'
    
    def set_M30(self, M30_df):
        self.M30 = M30_df
        self.last_update = 'M30'
    
    def set_H1(self, H1_df):
        self.H1 = H1_df
        self.last_update = 'H1'
    
    def set_H4(self, H4_df):
        self.H4 = H4_df
        self.last_update = 'H4'
    
    def set_D(self, D_df):
        self.D = D_df
        self.last_update = 'D'
    
    def set_W(self, W_df):
        self.W = W_df
        self.last_update = 'W'
    
    def set_M(self, M_df):
        self.M = M_df
        self.last_update = 'M'

class TickEvent(event):
    def __init__(self, instrument=None, price=None, time=None):
        self.type = 'tick_event'
        self.instrument = instrument
        self.price = price
        self.time = time
        
class IndicatorEvent(event):
    pass

class SignalEvent(event):
    def __init__(self,event=None,direction=None,granularity=None,strategy=None):
        self.type = 'signal_event'
        self.instrument = None
        #self.price = price
        self.time = None
        self.strategy = strategy
        self.granularity = granularity
        self.direction = direction
        self.instrument_data = event
        self.portfolio = None

class PortfolioEvent(event):
    def __init__(self, account):
        self.type = 'portfolio_event'
        self.balance = account.balance
        self.equity = account.NAV
        self.currency = account.currency
        self.used_margin = account.marginUsed
        self.margin_available = account.marginAvailable
        
        self.trades = account.trades
        self.trades_list = []
        
        if self.trades:
            for item in self.trades:
                if item.instrument not in self.trades_list:
                    self.trades_list.append(item.instrument)

        self.orders = account.orders
        
        self.orders_list = []
        if self.orders:
            for item in self.orders:
                if item.instrument not in self.orders_list:
                    self.orders_list.append(item.instrument)

        self.pl = account.pl
        self.unrealizedPL = account.unrealizedPL
        self.last_transactionID = account.lastTransactionID
        self.positions = account.positions
        self.positionValue = account.positionValue

class PositionEvent(event):
    def __init__(self, position):
        self.type = 'position_event'
        self.instrument = position.instrument
        self.margin_used = position.marginUsed
        #self.units = position.units
        self.pl = position.pl
        self.unPL = position.unrealizedPL
        self.long = position.long
        self.short = position.short

class TradeEvent(event):
    def __init__(self, trade):
        self.type = 'trade_event'
        self.id = trade.id
        self.state = trade.state
        self.instrument = trade.instrument
        self.margin_used = trade.marginUsed
        self.initial_units = trade.initialUnits
        self.current_units = trade.currentUnits
        self.price = trade.price
        self.open_time = trade.openTime
        self.tp_id=trade.takeProfitOrderID
        self.unPL=trade.unrealizedPL
  
class PendingOrderEvent(object):
    def __init__(self, order):
        self.type = 'pendingorder_event'  
        self.state = order.state
        self.id = order.id
        self.instrument = order.instrument
        self.price = order.price
        self.order_type = order.type
        self.units = order.units
        self.tp = order.takeProfitOnFill.price if order.takeProfitOnFill else None
        self.sl = order.stopLossOnFill.price if order.stopLossOnFill else None
        
class OrderEvent(event):
    def __init__(self):
        self.type = 'order_event'
        self.instrument = None
        self.time = None
        self.spread = None
        self.prices = None
        self.margin = None
        self.units = None
        self.trade_pip_values = None
        self.id = None
        self.strategy = None
        self.tp = None
        self.sl = None
        
        self.expected_profit = None
        self.expected_loss = None
        self.ok = False