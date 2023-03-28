import argparse
import queue
import threading
import time

from .common import config

from app.api import API_V20
from app.events import PortfolioEvent

from app.settings import api_connect

class Portfolio(object):
    def __init__(self):
        self.api = API_V20()
        self.account_id = self.api.account_id
        
        self.balance = None
        self.equity = None
        self.currency = None
        self.used_margin = None
        self.margin_available = None
        self.trades = None
        self.IDs = []
        self.positions = None

        self.orders = None
        
        self.pl = None
        self.unrealizedPL = None
        self.last_transactionID = None
        
        self.positionValue = None
        
        self.events_queue = queue
        self.tick_event = None

        #self.account = self.portfolio_init(self.events_queue)

    def update(self):
        def connection():
            return self.api.api.account.get(self.account_id)

        try:
            response = connection()

        except:
            time.sleep(api_connect)
            try:
                response = connection()
            except:
                time.sleep(api_connect)
                response = connection()
            
        #
        # Extract the Account representation from the response.
        #
        account = response.get("account", "200")
        
        self.balance = account.balance
        self.equity = account.NAV
        self.currency = account.currency
        self.used_margin = account.marginUsed
        self.margin_available = account.marginAvailable
        self.trades = account.trades

        self.trades_list = []
        self.orders_list = []

        self.positions_list=[]
        
        if self.trades:
            for item in self.trades:
                if item.instrument not in self.trades_list:
                    self.trades_list.append(item.instrument)
                
                if item.id not in self.IDs:
                    self.IDs.append(item.id)
        
        self.orders = account.orders
        if self.orders:
            for order in self.orders:
                if order.type != 'TAKE_PROFIT':
                    if order.type !='STOP_LOSS':
                        if order.instrument not in self.orders_list:
                            self.orders_list.append(order.instrument)

        if self.positions:
            for pos in self.positions:
                if pos.marginUsed:
                    if pos.instrument not in self.positions_list:
                        self.positions_list.append(pos.instrument)

        self.pl = account.pl
        self.unrealizedPL = account.unrealizedPL
        self.last_transactionID = account.lastTransactionID
        
        self.positions = account.positions
        
        self.positionValue = account.positionValue
        
        return