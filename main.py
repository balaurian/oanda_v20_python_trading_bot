import os
import time
import queue
import threading
import logging
import curses

from app.api import API_V20
from app.common.common_func import get_date
from app.events import TimeframeUpdateEvent
from app.executor import Executor
from app.history import History
from app.instruments_setup import InstrumentData
from app.money_management import MoneyManager
from app.portfolio import Portfolio
from app.price_stream import PriceStreamer
from app.spreads import Spreads
from app.strategies import Strategy

from app.json_handler import JsonHandler
from app.settings import *

def list_to_str(list_to_convert):
    ls_to_str = ''

    for i in range(0,len(list_to_convert)):
        if ls_to_str != '':
            ls_to_str = ','.join([ls_to_str, list_to_convert[i]])
            
        else:
            ls_to_str = list_to_convert[i]

    return ls_to_str

logging.basicConfig(filename='app/data/log.log',filemode='a',level=logging.INFO, format='%(asctime)-8s|%(name)-14s|%(levelname)-6s|%(message)-s')

#https://stackoverflow.com/questions/27774093/how-to-manage-logging-in-curses
class CursesHandler(logging.Handler):
    def __init__(self, screen):
        logging.Handler.__init__(self)
        self.screen = screen

    def emit(self, record):
        try:
            msg = self.format(record)
            screen = self.screen
            fs = "\n%s"
            screen.addstr(fs % msg)
            screen.refresh()

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            self.handleError(record)

M1=None
M5=None

class MainApp():
    def __init__(self,stdscr):
        
        self.stdscr = stdscr
        if curses.has_colors() == True:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            
            self.BLUE_WHITE = curses.color_pair(1)
        
        screen = curses.initscr()
        screen.nodelay(1)
        
        self.stdscr.clear()
        
        self.portfolio_win = curses.newwin(12,30,0,0)
        self.portfolio_win.bkgd(' ',self.BLUE_WHITE)
        
        self.event_win = curses.newwin(4,60,13,0)
        self.event_win.bkgd(' ',self.BLUE_WHITE)

        self.instr_win = curses.newwin(12,30,0,31)
        self.instr_win.bkgd(' ',self.BLUE_WHITE)
        
        self.signal_win = curses.newwin(12,30,0,62)
        self.signal_win.bkgd(' ',self.BLUE_WHITE)

        self.order_win = curses.newwin(12,30,0,93)
        self.order_win.bkgd(' ',self.BLUE_WHITE)

        self.logging_win = curses.newwin(1,60,18,0)
        
        self.logging_win.scrollok(True)
        self.logging_win.idlok(True)
        self.logging_win.leaveok(True)
        self.logging_win.setscrreg(0, 0)
        
        mh=CursesHandler(self.logging_win)
        formatterDisplay = logging.Formatter('%(asctime)-8s | %(levelname)-7s | %(message)-s', '%H:%M:%S')
        mh.setFormatter(formatterDisplay)
        self.logger = logging.getLogger(' ')
        self.logger.addHandler(mh)
        
        self.stdscr.noutrefresh()
        self.portfolio_win.noutrefresh()
        self.logging_win.noutrefresh()
        
        curses.doupdate()

        self.kill_threads = False # thread killswitch
        
        self.events_queue = queue.PriorityQueue()
        
        self.api=API_V20()
        self.account_id = self.api.account_id
        
        self.instruments = []
        self.session_total=0
        
        #setup portfolio at startup
        self.portfolio = Portfolio()
        self.portfolio.update()
        
        self.spreads = Spreads()

        self.strategy = Strategy()

        self.instrument_data = InstrumentData()

        self.money_manager=MoneyManager()

        self.execute = Executor()
        
        self.json_handler=JsonHandler()

        self.total_allowed = self.portfolio.equity*max_percent_total
        self.trade_allowed = self.total_allowed*max_percent_per_trade
        
        #self.timeframer = TimeframeUpdateEvent()
        self.M1,self.M5,self.M15,self.M30,self.H1,self.H4,self.D,self.W,self.M = 60,300,900,1800,3600,14400,86400,604800,2592000
        
        self.spreadEvents_list = self.spreads.select_instruments(instruments_number, self.portfolio.trades_list) #returns a list of SpreadEvent objects (instrument/spread/time)
        
        #get instruments list and convert list to string for price streaming
        for item in self.spreadEvents_list:
            if item.instrument not in self.instruments:
                self.instruments.append(item.instrument)

        self.instruments_to_str = list_to_str(self.instruments)
        self.portfolio_diplay()
        
        #init ticks 
        self.streamer = PriceStreamer(self.instruments_to_str,self.events_queue) 
        
        trade_thread = threading.Thread(target=self.event_handler) #Thread #1 - main event handler
        ticks_thread = threading.Thread(target=self.get_ticks_stream) #Thread #2 - tick streamer
        
        trade_thread.start()
        ticks_thread.start()
        
        #self.M1_update(self.M1)
        #self.M5_update(self.M5)

        while True:
            key = stdscr.getch()    # wait for a character; returns an int; does not raise an exception.
            if key == 0x1b:         # escape key exits
                self.kill_threads=True
                break
            
        trade_thread.join()
        ticks_thread.join()
        
        #M1.cancel()
        #M1.join()
        #M5.cancel()
        #M5.join()

    def get_ticks_stream(self):
        while (not self.kill_threads):
            self.streamer.ticks_handler()

    def timer(self,timeframe):
        #while (not self.kill_threads):
        timeframe_update_event = self.timeframer(timeframe)
        #t = threading.Timer(timeframe, self.timer, [timeframe])
        #t.start()
        self.events_queue.put((1,timeframe_update_event))

    def M1_update(self,timeframe):
        #https://stackoverflow.com/questions/9812344/cancellable-threading-timer-in-python
        #todo
        #https://www.section.io/engineering-education/how-to-perform-threading-timer-in-python/
        timeframe_update_event = TimeframeUpdateEvent(timeframe)
        global M1
        M1=threading.Timer(timeframe,self.M1_update,[timeframe])
        M1.start()
        self.events_queue.put((1,timeframe_update_event))
        print('m1 update')

    def M5_update(self,timeframe):
        timeframe_update_event = TimeframeUpdateEvent(timeframe)
        global M5
        M5=threading.Timer(timeframe,self.M5_update,[timeframe])
        M5.start()
        self.events_queue.put((1,timeframe_update_event))
        print('m5 update')

    def timeframes(self):
        M1,M5,M15,M30,H1,H4,D,W,M = 60,300,900,1800,3600,14400,86400,604800,2592000
        #while (not self.kill_threads):
        for tf in [M1, M5, M15, M30, H1, H4, D, W, M]:
            t = threading.Timer(tf, self.timer, [tf]) #Thread #3 // update history data ///
            t.start()
            if tf == 60:
                tf = 'M1'
            
            elif tf == 300:
                tf = 'M5'

            elif tf == 900:
                tf = 'M15'
            
            elif tf == 1800:
                tf = 'M30'
            
            elif tf == 3600:
                tf = 'H1'
            
            elif tf == 14400:
                tf = 'H4'
            
            elif tf == 86400:
                tf = 'D'
            
            elif tf == 604800:
                tf = 'W'
            
            elif tf == 2592000:
                tf = 'M'

            print (tf, 'thread started')
        
            #return t

    def portfolio_diplay(self):
        self.portfolio_win.erase()
        self.portfolio_win.border()
        self.portfolio_win.addstr(0,2,f' {self.account_id} ', curses.A_BOLD | curses.A_REVERSE)
        self.portfolio_win.addstr(1,1,f'equity: {round(self.portfolio.equity,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(2,1,f'unrealized p/l: {round(self.portfolio.unrealizedPL,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(3,1,f'session total: {round(self.session_total,3)} USD')
        self.portfolio_win.addstr(4,1,f'balance: {round(self.portfolio.balance,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(5,1,f'realized p/l: {round(self.portfolio.pl,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(6,1,f'position value: {round(self.portfolio.positionValue,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(7,1,f'used margin: {round(self.portfolio.used_margin,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(8,1,f'margin available: {round(self.portfolio.margin_available,2)} {self.portfolio.currency}')
        self.portfolio_win.addstr(9,1,f'trades: {len(self.portfolio.trades)} | instruments: {len(self.portfolio.trades_list)}')
        self.portfolio_win.addstr(10,1,f'30%: {round(self.total_allowed,2)} | 2%: {round(self.trade_allowed,2)}')
        self.portfolio_win.noutrefresh()

    def trades_diplay(self,event):
        if self.portfolio.trades:
            self.trades_win = curses.newwin(len(self.portfolio.trades)+4,100,0,34)
            #self.trades_win = curses.newwin(16,100,0,34)
            self.trades_win.scrollok(True)
            self.trades_win.bkgd(' ',self.BLUE_WHITE)
            self.trades_win.erase()
            self.trades_win.border()
            self.trades_win.addstr(1,2,f'  id   instrument     profit    units    direction  ', curses.A_UNDERLINE | curses.A_REVERSE)
            for i in range(0,len(self.portfolio.trades)):
                if self.portfolio.trades[i].state == 'OPEN':
                    self.trades_win.addstr(i+2,1,f'  {self.portfolio.trades[i].id}   {self.portfolio.trades[i].instrument}      {self.portfolio.trades[i].unrealizedPL}    {self.portfolio.trades[i].currentUnits}     {" long" if self.portfolio.trades[i].currentUnits>0 else "short"}')
                    self.trades_win.noutrefresh()

    def event_display(self, event):
        self.event_win.erase()
        self.event_win.border()
        self.event_win.addstr(0,2,f' events queue ')
        self.event_win.addstr(1,1,f'{event.type}      | last time: {event.time[:-9]}')
        self.event_win.addstr(2,1,f'{get_date()}')
        self.event_win.noutrefresh()

    def instrument_display(self, event):
        self.instr_win.erase()
        self.instr_win.border()
        self.instr_win.addstr(0,2,f' last instrument ')
        self.instr_win.addstr(1,1,f'{event.instrument}')
        self.instr_win.addstr(2,1,f'{event.ask} / {event.bid}')
        self.instr_win.addstr(4,1,f'spread {round(event.spread,2)}')
        self.instr_win.addstr(5,1,f'contract {event.contract_size}')
        self.instr_win.addstr(6,1,f'margin {round(event.margins[0],2)}')
        self.instr_win.addstr(7,1,f'pip val {round(event.pip_values[0],3)} / {round(event.pip_values[0],3)}')
        self.instr_win.addstr(8,1,f'pip loc {event.pip_location}')
        self.instr_win.addstr(9,1,f'margin rate {event.margin_rate}')
        self.instr_win.addstr(10,1,f'{event.time}')
        self.instr_win.noutrefresh()

    def signal_display(self, event):
        self.signal_win.erase()
        self.signal_win.border()
        self.signal_win.addstr(0,2,f' last signal ')
        self.signal_win.addstr(1,1,f'{event.instrument}')
        self.signal_win.addstr(2,1,f'')
        self.signal_win.addstr(3,1,f'strategy: {event.strategy}')
        self.signal_win.addstr(4,1,f'direction: {event.direction}')
        self.signal_win.addstr(5,1,f'granularity: {event.granularity}')
        self.signal_win.addstr(8,1,f'{event.time}')
        self.signal_win.noutrefresh()

    def order_display(self, event, reason):
        self.order_win.erase()
        self.order_win.border()
        self.order_win.addstr(0,2,f' last order ')
        self.order_win.addstr(1,1,f'{event.instrument}')
        self.order_win.addstr(2,1,f'margin: {round(event.margin,3)}')
        self.order_win.addstr(3,1,f'strategy: {event.strategy}')
        if event.units >0:
            self.order_win.addstr(4,1,f'buy {event.units}')
        
        else:
            self.order_win.addstr(4,1,f'sell {abs(event.units)} units')

        self.order_win.addstr(5,1,f'trade_pip_values: {round(event.trade_pip_value,3)}')
        self.order_win.addstr(6,1,f'expected profit: {round(event.expected_profit,3)}')
        self.order_win.addstr(8,1,f'{reason}')
        self.order_win.addstr(9,1,f'{event.time}')
        self.order_win.noutrefresh()

    def event_handler(self):
        while (not self.kill_threads):
            try:
                event = self.events_queue.get(False)
                
            except queue.Empty:
                self.logger.debug('queue empty')
            
            else:
                if event[1] is not None:
                    if event[1].type != 'timeframeupdate_event':
                        self.event_display(event[1])
                    self.logger.debug(f'{event[1].type}')
                    
                    if event[1].type == 'tick_event':
                        self.logger.debug(f'{event[1].type} :: {event[1].instrument}')
                        
                        self.portfolio.update()
                        self.portfolio_diplay()
                        
                        #read json
                        json_data=self.json_handler.json_data

                        if event[1].instrument in self.portfolio.trades_list:
                            for pos in self.portfolio.positions:
                                if pos.marginUsed:
                                    if event[1].instrument == pos.instrument:
                                        for i in range(0,len(json_data)):
                                            if event[1].instrument == json_data[i]['instrument']:
                                                if json_data[i]['active']:
                                                    if pos.long.units > abs(pos.short.units):
                                                        main_trade = pos.long
                                                        secondary_trade = pos.short

                                                    else:
                                                        main_trade = pos.short
                                                        secondary_trade = pos.long

                                                    if any(id in json_data[i]['IDs'] for id in self.portfolio.IDs):    
                                                        if json_data[i]['level'] == '1':
                                                            if round(pos.unrealizedPL/json_data[i]['pip value'],2) >= pip_tp:
                                                                #closing position (both buy/sell trades)
                                                                long_units=str(pos.long.units)
                                                                short_units=str(abs(pos.short.units))
                                                                close_pos = self.execute.close_position(pos.instrument,long_units=long_units,short_units=short_units)
                                                                
                                                                #if close_pos.status==200:
                                                                self.logger.info(f'376: closing position @lvl1 {pos.instrument} | {round(pos.unrealizedPL,3)} USD | {round(pos.unrealizedPL/json_data[i]["pip value"],2)} pips | long {long_units} | short {short_units}')
                                                            
                                                                #update json/save json
                                                                json_data[i]['realizedPL'] +=round(pos.unrealizedPL,3)
                                                                json_data[i]['realizedPL_pips'] +=round(pos.unrealizedPL/json_data[i]['pip value'],2)
                                                                
                                                                json_data[i]['active']=False
                                                                self.session_total +=round(pos.unrealizedPL,3)
                                                            
                                                                self.json_handler.json_write(json_data,self.json_handler.file_name)

                                                                time.sleep(5)
                                                                continue

                                                                # else:
                                                                #     self.logger.error(f'391: error {close_pos.status} closing lvl1 {pos.instrument} | {round(pos.unrealizedPL,3)} USD | {round(pos.unrealizedPL/json_data[i]["pip value"],2)} pips | long {long_units} | short {short_units}')
                                                                
                                                            elif round(secondary_trade.unrealizedPL*hedge_ratio/json_data[i]['pip value'],2) >=pip_tp*2:
                                                                #close secondary_trade
                                                                for trade in self.portfolio.trades:
                                                                    if trade.id in secondary_trade.tradeIDs:
                                                                        close_trade = self.execute.close_trade(trade.id, str(abs(trade.currentUnits)))
                                                                        if close_trade.status==200:
                                                                            self.logger.info(f'399:closing second trade {pos.instrument} | id {trade.id} | {trade.currentUnits} units | {round(secondary_trade.unrealizedPL*hedge_ratio/json_data[i]["pip value"],2)} pips | {round(secondary_trade.unrealizedPL,3)} USD')
                                                                        
                                                                        else:
                                                                            self.logger.error(f'402:closing {pos.instrument}, id: {trade.id}, units:{trade.currentUnits} was not possible:{response}')

                                                                json_data[i]['realizedPL'] +=round(secondary_trade.unrealizedPL,3)
                                                                json_data[i]['realizedPL_pips'] +=round(secondary_trade.unrealizedPL*hedge_ratio/json_data[i]['pip value'],2)
                                                                self.session_total +=round(secondary_trade.unrealizedPL,3)
                                                                
                                                                #open another trade with trade main_trade.units
                                                                response=self.execute.open_trade(pos.instrument,json_data[i]['main_trade_units'])
                                                                if response.status == 201:
                                                                    price = response.body['orderFillTransaction'].price
                                                                    reason = response.body['orderFillTransaction'].reason #MARKET_ORDER
                                                                    marginreq=response.body['orderFillTransaction'].tradeOpened.initialMarginRequired
                                                                    
                                                                    self.logger.info(f'415: lvl2: {reason} {pos.instrument} | {response.body["lastTransactionID"]} | {price} | {marginreq} USD | units {json_data[i]["main_trade_units"]}')
                                                                
                                                                #update json
                                                                json_data[i]['level'] = '2'
                                                                json_data[i]['active']=True
                                                                if response.body['lastTransactionID'] not in json_data[i]['IDs']:
                                                                    json_data[i]['IDs'].append(response.body['lastTransactionID'])

                                                                self.json_handler.json_write(json_data,self.json_handler.file_name)

                                                                self.portfolio.update()
                                                                self.portfolio_diplay()

                                                                continue
                                                        
                                                        elif json_data[i]['level'] != '1':
                                                            if round(main_trade.unrealizedPL/json_data[i]['pip value'],2) + json_data[i]['realizedPL_pips'] >= minimum_profit:
                                                                #close position (all same direction trades)
                                                                for trade in self.portfolio.trades:
                                                                    if trade.id in main_trade.tradeIDs:
                                                                        close_trade = self.execute.close_trade(trade.id, str(abs(trade.currentUnits)))
                                                                        
                                                                        #if close_trade==201:
                                                                        self.logger.info(f'438: closing lvl{json_data[i]["level"]} {pos.instrument} | {round(main_trade.unrealizedPL,3)} USD | {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pips | id {trade.id} | {trade.currentUnits} units')
                                                                        
                                                                        #else:
                                                                        #    self.logger.error(f'441: closing lvl{json_data[i]["level"]} {pos.instrument} | {round(main_trade.unrealizedPL,3)} USD | {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pips | id {trade.id} | {trade.currentUnits} units was not possible: {response}')
                                                                    if secondary_trade.tradeIDs:
                                                                        if trade.id in secondary_trade.tradeIDs:
                                                                            close_trade = self.execute.close_trade(trade.id, str(abs(trade.currentUnits)))
                                                                            
                                                                            #if close_trade==201:
                                                                            self.logger.info(f'447: closing lvl{json_data[i]["level"]} {pos.instrument} | {round(main_trade.unrealizedPL,3)} USD | {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pips | id {trade.id} | {trade.currentUnits} units')

                                                                #update json
                                                                json_data[i]['active']=False
                                                                json_data[i]['realizedPL'] +=round(main_trade.unrealizedPL,3)
                                                                json_data[i]['realizedPL_pips'] +=round(main_trade.unrealizedPL/json_data[i]['pip value'],2)
                                                                
                                                                self.json_handler.json_write(json_data,self.json_handler.file_name)
                                                                
                                                                self.session_total +=main_trade.unrealizedPL

                                                                self.portfolio.update()
                                                                self.portfolio_diplay()
                                                                
                                                                time.sleep(5)
                                                                continue
                                                        
                                                        if json_data[i]['level'] == '2':
                                                            if round(main_trade.unrealizedPL/json_data[i]['pip value'],2) < -1*pip_sl*5:
                                                                #open new trade
                                                                response=self.execute.open_trade(pos.instrument,json_data[i]['main_trade_units'])
                                                                if response.status == 201:
                                                                    price = response.body['orderFillTransaction'].price
                                                                    reason = response.body['orderFillTransaction'].reason #MARKET_ORDER
                                                                    marginreq=response.body['orderFillTransaction'].tradeOpened.initialMarginRequired
                                                                    
                                                                    self.logger.info(f'lvl3: {reason} {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pip | {pos.instrument} | {response.body["lastTransactionID"]} | {price} | {marginreq} USD | units {json_data[i]["main_trade_units"]}')
                                                                    
                                                                    #update json
                                                                    json_data[i]['level'] = '3'
                                                                    #update trades ids list
                                                                    if response.body['lastTransactionID'] not in json_data[i]['IDs']:
                                                                        json_data[i]['IDs'].append(response.body['lastTransactionID'])
                                                                    
                                                                    self.json_handler.json_write(json_data,self.json_handler.file_name)
                                                                    
                                                                    self.portfolio.update()
                                                                    self.portfolio_diplay()

                                                                    continue

                                                                else:
                                                                    self.logger.error(f'lvl3: {reason} failed with {response.status} {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pip | {pos.instrument} | {response.body["lastTransactionID"]} | {price} | {marginreq} USD | units {json_data[i]["main_trade_units"]}')

                                                        elif json_data[i]['level'] == '3':
                                                            if round(main_trade.unrealizedPL/json_data[i]['pip value'],2) < -1*pip_sl*10:
                                                                #open fourth trade
                                                                response=self.execute.open_trade(pos.instrument,json_data[i]['main_trade_units'])
                                                                if response.status == 201:
                                                                    price = response.body['orderFillTransaction'].price
                                                                    reason = response.body['orderFillTransaction'].reason #MARKET_ORDER
                                                                    marginreq=response.body['orderFillTransaction'].tradeOpened.initialMarginRequired
                                                                    
                                                                    self.logger.info(f'491: lvl4: {reason} {round(main_trade.unrealizedPL/json_data[i]["pip value"],2)} pip | {pos.instrument} | {response.body["lastTransactionID"]} | {price} | {marginreq} USD | units {json_data[i]["main_trade_units"]}')
                                                                
                                                                #update json
                                                                json_data[i]['level']='4'
                                                                #update trades ids list
                                                                if response.body['lastTransactionID'] not in json_data[i]['IDs']:
                                                                    json_data[i]['IDs'].append(response.body['lastTransactionID'])
                                                                
                                                                self.json_handler.json_write(json_data,self.json_handler.file_name)
                                                                
                                                                #update ui
                                                                self.portfolio.update()
                                                                self.portfolio_diplay()

                                                                #continue
                        
                        else:
                            instrument_event=self.instrument_data.instrument_setup(event[1].instrument)
                            self.instrument_display(instrument_event)
                            self.strategy.event_handler(instrument_event,self.events_queue)

                    elif event[1].type == 'signal_event':
                        self.signal_display(event[1])
                        
                        self.portfolio.update()
                        #add portfolio needed for money management
                        event[1].portfolio = self.portfolio
                        
                        if event[1].instrument not in self.portfolio.trades_list:
                            orders_pair_events=self.money_manager.orders_pair_setup(event[1])
                            responses =[]
                            for order in orders_pair_events:
                                response=self.execute.market(order)
                                self.order_display(order,response.reason)
                                order.id = response.body['lastTransactionID']
                                if response.status == 201:
                                    price = response.body['orderFillTransaction'].price
                                    reason = response.body['orderFillTransaction'].reason #MARKET_ORDER
                                    marginreq=response.body['orderFillTransaction'].tradeOpened.initialMarginRequired
                                    half_spread_cost=response.body['orderFillTransaction'].tradeOpened.halfSpreadCost
                                    order.margin = marginreq
                                    order.prices = price
                                    logging.info(f'{order.type} {reason} {order.instrument} | {order.id} | {price} | {marginreq} USD | units {order.units} | expected {order.expected_profit} USD')    

                                responses.append(response)

                            if responses[0].status == 201 and responses[1].status == 201:
                                self.json_handler.order_data_setup(orders_pair_events)
                                
                            else:
                                logging.error(f'cant open {event[1].instrument} from {event[1].type}')    
                                
                            self.portfolio.update()
                            self.portfolio_diplay()

                        else:
                            #read json
                            json_data=self.json_handler.json_data
                            for i in range(0,len(json_data)):
                                if event[1].instrument == json_data[i]['instrument']:
                                    if json_data[i]['active']:
                                        logging.warning(f'{event[1].type}: {event[1].instrument} - already opened says @json_data')    
                                    
                                    else:
                                        logging.warning(f'{event[1].type}: {event[1].instrument} - inactive says @json_data') 
                                        
                    else:
                        logging.info(f'{event[1].type}')

                else:
                    logging.warning("event is none")
            
            self.stdscr.noutrefresh()
            curses.doupdate()

            time.sleep(heartbeat)

if __name__ == '__main__':
    #https://stackoverflow.com/questions/60468019/python3-curses-with-threading
    os.environ.setdefault('ESCDELAY','100') # in mS; default: 1000
    curses.wrapper(MainApp)