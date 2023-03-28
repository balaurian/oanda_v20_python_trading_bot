import os
import json

class JsonHandler():
    def __init__(self):
        self.file_name='orders_data.json'
       
        try:
            with open(f'app/data/{self.file_name}','r') as jfile:
                self.json_data=json.load(jfile)
        
        except IOError:
                self.json_data=[]
                self.json_write(self.json_data,self.file_name)
        
    def order_data_setup(self,event):
        order_detail = {
            'instrument':event[0].instrument,
            'active':True,
            'level':'1',
            'IDs':[event[0].id,event[1].id],
            'price':[event[0].prices,event[1].prices],
            'margin':[event[0].margin,event[1].margin],
            'pip value':event[0].trade_pip_value,
            'expected_profit':[event[0].expected_profit,event[1].expected_profit],
            'expected_loss':[event[0].expected_loss,event[1].expected_loss],
            'main_trade_units':event[0].units,
            'sec_trade_units':event[1].units,
            # 'II_units':0,
            # 'III_units':0,
            # 'IV_units':0,
            'realizedPL':0,
            'realizedPL_pips':0
        }
        self.json_data.append(order_detail)
        
        self.json_write(self.json_data,self.file_name)
    
    def json_write(self,file_data,file):
        file_data=json.dumps(file_data,indent=4)
        with open(f'app/data/{file}','w')as output:
            output.write(file_data)