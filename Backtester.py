"""
    By Al Sabawi
    2023-03-11 
"""
import pandas as pd
import numpy as np
import matplotlib
# matplotlib.use('Agg')  # Use the 'Agg' backend for non-GUI environments
import matplotlib.pyplot as plt

from datetime import datetime
import pytz
import holidays
from termcolor import colored as cl
import warnings
from functools import wraps
import io
from flask import Flask, request, send_file, jsonify


def suppress_warnings(func):
  """Decorator to suppress warnings within a function."""
  @wraps(func)
  def wrapper(*args, **kwargs):
    with warnings.catch_warnings():
      warnings.filterwarnings("ignore", category=FutureWarning)
      return func(*args, **kwargs)
  return wrapper


class SignalsBacktester:
    """This class provides functions to backtest a set of signals in a daily datetime indexed pandas 
    DatafFrame against a daily stock prices DataFrame and returns the resulted returns in another DataFrame 
    """
    def __init__(self,df_in,signals,start_date=None,end_date=None,amount=100000):
        """Initialization requires the daily prices which includes the datetime type daily index and the 'Close' column as floats

        Args:
            df_in (_type_): pandas DataFrame of the End-Of-Day (EOD) stock prices
            signals (_type_): pandas Series of 1's and 0's where 1=Buy, 0=Sell or Don't buy
            start_date (_type_, optional): String in the date format "%Y-%m-%d". Defaults to None.
            end_date (_type_, optional):  String in the date format "%Y-%m-%d". Defaults to None.
            amount (int, optional): int. The initial investment. Defaults to 100000.
        """
        self.df_in = df_in
        self.signals = pd.DataFrame(signals,columns=['Predicted'],index=self.df_in.index)
        self.print_details = True
        self.amount = amount
        self.tran_history = pd.DataFrame()
        self.buy_and_hold_results = pd.DataFrame()
        
        # Fix the start and end dates to be Business days
        if start_date:
            self.start_date = self.next_business_day(start_date)
        else:
            self.start_date = self.df_in.index[0].strftime("%Y-%m-%d")
            
        if end_date:
            self.end_date = self.next_business_day(end_date)   
        else:
            self.end_date = self.df_in.index[-1].strftime("%Y-%m-%d")
            
        # print(f"Start Business Date = {self.start_date}")
        # print(signals)
            
    def set_print_details(self,print_details):
        self.print_details = print_details
        
    def set_tran_history(self, tran_history):
        self.tran_history = tran_history
    
    def get_tran_history(self):
        return self.tran_history
    
    def DatesRange(self,df):
        start = self.start_date
        end = self.end_date
        
        if start :
            start = pytz.utc.localize( datetime.fromisoformat(  start)).strftime("%Y-%m-%d")
        else:
            start = df.index[0]

        if end :
            end = pytz.utc.localize( datetime.fromisoformat( end)).strftime("%Y-%m-%d")
        else:
            end = pytz.utc.localize(datetime.today()).strftime("%Y-%m-%d")

        return df.loc[(df.index >= start) & (df.index <= end)].copy()

    @suppress_warnings
    def backtest(self):

        df_bt = self.df_in.join(self.signals, how='outer').fillna(method='ffill')
        df_bt = self.DatesRange(df_bt)
        
        if(len(df_bt)<2):
            return df_bt
        
        
        df_transactions = pd.DataFrame(np.zeros((len(df_bt), 9)),
                                    columns=['Buy_Count','Buy_Amount','Sell_Count','Sell_Amount',
                                                'Shares_Count','Cash_Balance','Buy_Hold','Account_Value','ROI_pcnt'],index=df_bt.index)
        # df_transactions.fillna(method='ffill')
        # print(df_transactions)
        
        # df_transactions.iloc[0].Cash_Balance = self.amount
        for i in range(0,len(df_bt)):
            
            if i == 0:
                df_transactions.iloc[i].Cash_Balance = self.amount
                df_transactions.iloc[i].Shares_Count = 0
                df_transactions.iloc[i].Buy_Hold = self.amount
            else:
                if i == 1:
                    buy_hold_shares = int(self.amount / df_bt.iloc[i].Open) 
                    init_buy_hold = round(buy_hold_shares *  df_bt.iloc[i].Open,2)
                    remained_buy_hold = self.amount - init_buy_hold
                    
                df_transactions.iloc[i].Buy_Hold = round(buy_hold_shares *  df_bt.iloc[i].Close + remained_buy_hold,2)
                
                df_transactions.iloc[i].Cash_Balance = df_transactions.iloc[i-1].Cash_Balance
                df_transactions.iloc[i].Shares_Count = df_transactions.iloc[i-1].Shares_Count
            
            # print(f"df_bt.iloc[i-1] , date {df_bt.iloc[i-1]}, predicted {df_bt.iloc[i-1].Predicted}")
            
            # print(i, df_transactions.iloc[i].Cash_Balance)
            
            if df_bt.iloc[i].Predicted == 1.0:
                shares_to_buy = int(df_transactions.iloc[i].Cash_Balance / df_bt.iloc[i].Open)
                if(shares_to_buy > 0):
                    cost_of_shares = round(shares_to_buy * df_bt.iloc[i].Open,2)
                    df_transactions.iloc[i].Buy_Count = int(shares_to_buy)
                    df_transactions.iloc[i].Buy_Amount = cost_of_shares
                    df_transactions.iloc[i].Cash_Balance = df_transactions.iloc[i].Cash_Balance - cost_of_shares
                    # print(df_transactions.iloc[i+1].Cash_Balance)
                    df_transactions.iloc[i].Shares_Count = int(shares_to_buy + df_transactions.iloc[i].Shares_Count)
            if df_bt.iloc[i].Predicted == 0.0:
                if df_transactions.iloc[i].Shares_Count > 0:
                    proceeds_of_sale = round(df_transactions.iloc[i].Shares_Count * df_bt.iloc[i].Open,2)
                    df_transactions.iloc[i].Sell_Amount = proceeds_of_sale
                    df_transactions.iloc[i].Cash_Balance = df_transactions.iloc[i].Cash_Balance + proceeds_of_sale
                    # print(df_transactions.iloc[i+1].Cash_Balance)
                    df_transactions.iloc[i].Sell_Count = df_transactions.iloc[i].Shares_Count
                    df_transactions.iloc[i].Shares_Count = 0
            
            df_transactions.iloc[i].Account_Value = round(df_transactions.iloc[i].Cash_Balance + \
                                                    (df_transactions.iloc[i].Shares_Count *  df_bt.iloc[i].Close),2)
            df_transactions.iloc[i].ROI_pcnt = round( ((df_transactions.iloc[i].Account_Value/self.amount) -1)*100,2)
            
            # print(f" {df_transactions.index[i]}")
        self.set_tran_history(df_transactions)
        
        # df_bt = df_bt.join(df_transactions, how='outer').fillna(method='ffill')
        df_bt = df_bt.join(df_transactions, how='outer')
        
        self.set_buy_and_hold_results()
        
        # print("df_bt",df_bt)
        return df_bt

    def next_business_day(self,date_str, country="US"):
        date = pd.to_datetime(date_str)
        holiday_dates = holidays.CountryHoliday(country, years=date.year).keys()
        while date.weekday() >= 5 or date.strftime("%Y-%m-%d") in holiday_dates:
            date = date + pd.tseries.offsets.BDay()
            
        if date not in self.df_in.index:
            for d in self.df_in.index:
                if d > date:
                    date = d
                    break
                
        return date.strftime("%Y-%m-%d")
    
    def buy_and_hold_strategy(self):
        # df_prices ,start_date=None, end_date=None, amount=100000
        # Buy and hold
        
        # Find the position of self.start_date in the index
        position = self.df_in.index.get_loc(self.start_date)

        # Increment the position to get the next date
        next_position = position + 1

        # Check if the next position is within the bounds of the DataFrame index
        if next_position < len(self.df_in.index):
            self.start_date = self.df_in.index[next_position]
        else:
            raise ValueError("The start_date is the last date in the DataFrame, no next date available.")

        first_day_open = round(self.df_in.loc[self.start_date].Open,2)
        number_of_shares = int(self.amount/first_day_open)
        cost_of_shares = round(first_day_open * number_of_shares,2)
        cash_balance = round(self.amount - cost_of_shares,2)
        value_of_shares_last_day = round(number_of_shares * self.df_in.iloc[-1].Close,2)
        account_value = round(cash_balance+value_of_shares_last_day,2)
        buy_and_hold_ROI = round( ( float(account_value/self.amount) - 1.0)*100 ,2)
        
        if self.print_details:
            print("\n")
            print(f"First Day Share Price at Open= ${round(first_day_open,2)}")
            print(f"Buy {number_of_shares} on {self.start_date}")
            print(f"Cost of Shares = ${cost_of_shares}")
            print(f"Remaining Cash Balance = {cash_balance}")
            print(f"Value of at Close share on {self.df_in.index[-1]} = {value_of_shares_last_day}")
            print(f"Last Day Share Price at Close= ${self.df_in.iloc[-1].Close}")
            print(f"Last Account Value = {account_value}")
            print(f"Buy and Hold ROI = {buy_and_hold_ROI}%")
        
        return buy_and_hold_ROI, account_value

    def set_buy_and_hold_results(self):

        self.start_date = self.df_in.index[1].strftime("%Y-%m-%d")
        
        first_day_open = round(self.df_in.loc[self.start_date].Open,2)
        number_of_shares = int(self.amount/first_day_open)
        cost_of_shares = round(first_day_open * number_of_shares,2)
        cash_balance = round(self.amount - cost_of_shares,2)
        last_date_of_close = self.df_in.index[-1].strftime("%Y-%m-%d")
        value_of_shares_last_day = round(number_of_shares * self.df_in.iloc[-1].Close,2)
        account_value = round(cash_balance+value_of_shares_last_day,2)
        buy_and_hold_ROI = round( ( float(account_value/self.amount) - 1.0)*100 ,2)
        last_day_close_price = round(self.df_in.iloc[-1].Close,2)
        
        self.buy_and_hold_results = {
            'first_day_open' : first_day_open,
            'number_of_shares' : number_of_shares,
            'cost_of_shares' : cost_of_shares,
            'cash_balance' : cash_balance,
            'last_date_of_close' : last_date_of_close,
            'value_of_shares_last_day' : value_of_shares_last_day,
            'account_value' : account_value,
            'buy_and_hold_ROI' : buy_and_hold_ROI,
            'last_day_close_price' : last_day_close_price
        }
        
        return self.buy_and_hold_results
        
    def buy_and_hold_strategy_html(self):
        # df_prices ,start_date=None, end_date=None, amount=100000
        # Buy and hold

        self.start_date = self.df_in.index[1].strftime("%Y-%m-%d")
        
        output = ''
        
        if self.print_details:
            output += ("<br>")
            output += (f"First Day Share Price at Open = ${round(self.buy_and_hold_results['first_day_open'],2)}<br>")
            output += (f"Buy {self.buy_and_hold_results['number_of_shares']} on {self.start_date}<br>")
            output += (f"Cost of Shares = ${self.buy_and_hold_results['cost_of_shares']}<br>")
            output += (f"Remaining Cash Balance = {self.buy_and_hold_results['cash_balance']}<br>")
            output += (f"Share Price on at Close {self.buy_and_hold_results['last_date_of_close']} is {self.buy_and_hold_results['last_day_close_price']}<br>")
            output += (f"Total 'Shares Only' Value at Close on {self.buy_and_hold_results['last_date_of_close']} is {self.buy_and_hold_results['value_of_shares_last_day']}<br>")
            output += (f"Total Account Value on {self.buy_and_hold_results['last_date_of_close']} EOD Close = ${self.buy_and_hold_results['account_value']} (Shares Only + Cash)<br>")
            # output += (f"Last Account Value = {account_value}<br>")
            output += (f"Buy and Hold ROI = {self.buy_and_hold_results['buy_and_hold_ROI']}% (Account Cash Included)<br><br>")
        
        return output,self.buy_and_hold_results['buy_and_hold_ROI'], self.buy_and_hold_results['account_value']


    def plot_account(self,stock=None):
        buyhold_account = pd.DataFrame(index=self.df_in.index,columns=["BuyHoldValue"])
        print(buyhold_account)
        buyhold_account = self.DatesRange(buyhold_account)
        
        close_changes = self.df_in.Close.pct_change().copy()
        close_changes = self.DatesRange(close_changes)
        
        buyhold_account.iloc[0].BuyHoldValue = self.amount
        # print(buyhold_account)
        
        for i in range(1,len(buyhold_account)):
            buyhold_account.iloc[i].BuyHoldValue = buyhold_account.iloc[i-1].BuyHoldValue + \
            (close_changes.iloc[i] * buyhold_account.iloc[i-1].BuyHoldValue)
        
        # print(buyhold_account)
        ax = self.tran_history[['Account_Value']][1:].plot(figsize=(15,8),grid=True)
        buyhold_account.plot(ax=ax)
        
        plt.grid(axis='both')
        plt.legend(title='Investment Accounts:')
        if stock:
            plt.title(f"{stock} AI vs Buy&Hold",fontsize = 14, fontweight ='bold')
        else:
            plt.title(f"AI vs Buy&Hold",fontsize = 14, fontweight ='bold')
            
        plt.show()
        
    def plot_account_image(self, stock=None, show_image=False):
        # print("in plot_account_image() Hi World",flush=True)

        tmp_trans_hist = self.get_tran_history()
        if(tmp_trans_hist.shape[0] == 0):
            img = io.BytesIO()
            return img
        
        # print(tmp_trans_hist["Account_Value"])
        # trans_hist = tmp_trans_hist.iloc[1:]
        trans_hist = tmp_trans_hist
        
        shares_to_buy = int(tmp_trans_hist.iloc[1].Buy_Hold / self.df_in.iloc[1].Open)
        # print(f"\nDate={tmp_trans_hist.index[1]}, Share Price = {self.df_in.iloc[1].Open}, number of share = {shares_to_buy}\n")
        
        # print(trans_hist.Buy_Hold)
        
        plt.figure(figsize=(12, 6))
        plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray')
        if stock:
            plt.title(f"{stock} AI vs Buy&Hold", fontsize=14, fontweight='bold')
        else:
            plt.title(f"AI vs Buy&Hold", fontsize=14, fontweight='bold')
        
        # Add labels for x and y axes
        plt.xlabel('Date')  # Label for x-axis
        plt.ylabel('Account Value')  # Label for y-axis
        
        plt.plot(trans_hist.Buy_Hold, label="Buy and Hold", color='blue', linestyle='-', linewidth=1.5)
        idx= trans_hist.index[1]
        plt.text(idx, trans_hist.loc[idx, 'Buy_Hold'], 
                        f'${self.df_in.loc[idx, "Open"]:.2f}\n{idx.strftime("%Y-%m-%d")}', 
                        color='blue', fontsize=11, ha='left', va='bottom')

        idx= trans_hist.index[-1]
        plt.text(idx, trans_hist.loc[idx, 'Buy_Hold'], 
                        f'${self.df_in.loc[idx, "Open"]:.2f}\n{idx.strftime("%Y-%m-%d")}', 
                        color='blue', fontsize=10, ha='left', va='bottom')        
        
        # t_hist = self.tran_history[1:] 
        plt.plot(trans_hist['Account_Value'],label='Account Value', color='red', linestyle='--', linewidth=1.5)
        plt.text(idx, trans_hist.loc[idx, 'Account_Value'], 
                f'${self.df_in.loc[idx, "Open"]:.2f}\n{idx.strftime("%Y-%m-%d")}', 
                color='red', fontsize=10, ha='left', va='bottom')
        
        # Plot the buy signals
        buy_signals = trans_hist[trans_hist['Buy_Count'] > 0]
        for idx, row in buy_signals.iterrows():
            if idx in self.df_in.index:
                plt.scatter(idx, trans_hist.loc[idx, 'Account_Value'], marker='^', color='green', s=100)
                plt.text(idx, trans_hist.loc[idx, 'Account_Value'], 
                        f'${self.df_in.loc[idx, "Open"]:.2f}\n{idx.strftime("%Y-%m-%d")}', 
                        color='green', fontsize=10, ha='left', va='bottom')

        # Plot the sell signals
        sell_signals = trans_hist[trans_hist['Sell_Count'] > 0]
        for idx, row in sell_signals.iterrows():
            if idx in self.df_in.index:
                plt.scatter(idx, trans_hist.loc[idx, 'Account_Value'], marker='v', color='red', s=100)
                plt.text(idx, trans_hist.loc[idx, 'Account_Value'], 
                        f'${self.df_in.loc[idx, "Open"]:.2f}\n{idx.strftime("%Y-%m-%d")}', 
                        color='red', fontsize=10, ha='left', va='top')
                
                
        # Create and Customize a legend
        handles, labels = plt.gca().get_legend_handles_labels()
        legend = plt.legend(handles=handles, labels=labels, title='Investment Accounts:', loc='upper left', bbox_to_anchor=(1, 1))
    
        # Add text below the legend
        additional_text = f"Start:${self.amount}\nAI Strategy:${trans_hist.Account_Value.iloc[-1]} %{trans_hist.ROI_pcnt.iloc[-1]}\nBuy & Hold:${self.buy_and_hold_results['account_value']} %{self.buy_and_hold_results['buy_and_hold_ROI']}"
        plt.gca().add_artist(legend)  # Add the legend to the plot
        plt.text(1.01, 0.5, additional_text, transform=plt.gca().transAxes, fontsize=10, verticalalignment='top')

        # plt.legend(title='Investment Accounts:\nOpen Share Price $', loc='upper left', bbox_to_anchor=(1, 1))  # Adjust legend position
        # plt.legend(title='Investment Accounts:', loc='upper left')  # Adjust legend position
    
        # Customize axes (optional)
        plt.xticks(rotation=45)  # Rotate x-axis tick labels for better readability (optional)
        plt.tight_layout()  # Adjust spacing to prevent overlapping elements (optional)

        # Major and minor ticks (optional)
        # plt.locator_params(axis='x', nbins=7)  # Adjust the number of major x-axis ticks
        # plt.locator_params(axis='y', nbins=5)  # Adjust the number of major y-axis ticks
        plt.minorticks_on()  # Enable minor ticks on both axes

        if not show_image:
            # Save the plot to a BytesIO object
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            # print("End Hi World",flush=True)
        
            # print(img.getvalue())
            return img
        else:
            plt.show()


        
    @suppress_warnings
    def run(self):
        """Generate the backtesting calculations and return a pandas DataFrame with the results 
        """
        # invest_mount = 100000
        # start_date = '2022-09-01'

        print(f"Start Investment Date : {self.start_date}")
        print(f"Investment Amount : ${self.amount}")

        # df_tran = backtest(df_in,df_pred1.Predicted,start_date='2022-01-01',end_date='2023-01-01')
        df_tran = self.backtest()
        returns = df_tran.ROI_pcnt[-1]
        buy_and_hold_ROI,ending_account_value = self.buy_and_hold_strategy()
        if returns > buy_and_hold_ROI:
            on_color = 'on_green'
        else:
            on_color = 'on_red'
            
        print(cl(f"\nAI PREDICTION ENGINE Strategy:\n\tReturn on Investment : {returns}%\n\tEnding Account Value : ${df_tran['Account_Value'].iloc[-1]}",attrs=['bold'],on_color=on_color))

        # print(df_tran[['Open','Close','Predicted','Buy_Count','Buy_Amount',
        #          'Sell_Count','Sell_Amount','Shares_Count','Cash_Balance','Account_Value','ROI_pcnt']].tail(30))

        print(f"\nBUY & HOLD Strategy:\n\tReturn on Investment : {buy_and_hold_ROI}%\n\tEnding Account Value : ${ending_account_value}")

    @suppress_warnings
    def run_html(self,stock='N/A'):
        """Generate the backtesting calculations and return a pandas DataFrame with the results 
        """
        # invest_mount = 100000
        # start_date = '2022-09-01'

        output = f'<h2 style="text-decoration: underline;">Backtesting this Strategy on {stock}</h2><b>'
        output += (f"Start Investment Date : {self.start_date}<br>")
        output += (f"Investment Amount : ${self.amount}")
        output += "<ul>"

        # df_tran = backtest(df_in,df_pred1.Predicted,start_date='2022-01-01',end_date='2023-01-01')
        df_tran = self.backtest()
        
        # Quit if there are less than 2 transactions 
        if(len(df_tran)<2):
            return output
        
        returns = df_tran.ROI_pcnt[-1]
        html_output,buy_and_hold_ROI,ending_account_value = self.buy_and_hold_strategy_html()
        output += html_output
        
        if returns > buy_and_hold_ROI:
            on_color = 'green'
        else:
            on_color = 'red'
            
        output += (f"<div style='background:{on_color};color:white'><h3 style='background:{on_color};color:white'>AI PREDICTION ENGINE Strategy:</h3>Return on Investment : {returns}%<br>Ending Account Value : ${df_tran['Account_Value'].iloc[-1]}<br></div>")

        output += (f"<div><h3>BUY & HOLD Strategy:</h3>Return on Investment : {buy_and_hold_ROI}%<br>Ending Account Value : ${ending_account_value}</b></div>")
        output += "</ul><hr>"
        return output


    def results(self):
        tran_history = self.get_tran_history()

        max_account_value = tran_history[(tran_history['Account_Value'] == tran_history['Account_Value'].max())]
        if tran_history['Buy_Count'].sum() > 0:
            first_buy = tran_history[(tran_history['Buy_Count']>0)].index[0].strftime("%Y-%m-%d")
        else:
            first_buy = 'None'
        buys = len(tran_history[tran_history['Buy_Count']>0])
        sells = len(tran_history[tran_history['Sell_Count']>0])
        days_bought_or_sold = tran_history[(tran_history['Buy_Count'] > 0) | (tran_history['Sell_Count'] > 0)]

        # If no transactions, exit now else show transaction table
        if buys == 0 :
            return
        
        print(cl("************************************************************",attrs=['bold']))
        print(cl("**                        RESULTS                         **",attrs=['bold'],on_color='on_blue'))       
        print(cl("************************************************************",attrs=['bold']))
        print("\nFirst Buy On:",first_buy)
        print(f"Number of Buy Transactions : {buys}")
        print(f"Number of Sell Transactions : {sells}")
        print(f"Number of Days Transactions Happened : {len(days_bought_or_sold)} out of {len(tran_history)} Trading Days")

        trans_from_first_buy = tran_history.loc[first_buy:]
        lowest_account_value = trans_from_first_buy[(trans_from_first_buy['Account_Value'] == trans_from_first_buy['Account_Value'].min())]
        max_drawdown = tran_history[(tran_history['ROI_pcnt'] == tran_history['ROI_pcnt'].min())]
        highest_ROI = tran_history[(tran_history['ROI_pcnt'] == tran_history['ROI_pcnt'].max())]

        print(f"\nPeak Account Value was on {max_account_value.index[0].strftime('%Y-%m-%d')} : ${max_account_value.iloc[0].Account_Value}")
        print(f"Lowest Account Value was on {lowest_account_value.index[0].strftime('%Y-%m-%d')} : ${lowest_account_value.iloc[0].Account_Value}")

        print(f"\nHighest ROI (Max % Return) was on {highest_ROI.index[0].strftime('%Y-%m-%d')} : {highest_ROI.iloc[0].ROI_pcnt}%")
        print(f"Lowest ROI (Max % Drawdown) was on {max_drawdown.index[0].strftime('%Y-%m-%d')} : {max_drawdown.iloc[0].ROI_pcnt}%")

        print(cl("************************************************************",attrs=['bold']))
        print(cl("**                   TRANSACTION TABLE                    **",attrs=['bold'],on_color='on_blue')) 
        print(cl("************************************************************",attrs=['bold']))
        print(tran_history)


    def results_html(self,stock):
        tran_history = self.get_tran_history()
        
        # if there are less than 2 transactions we cannot backtest and we need to quit
        # print(tran_history)
        if(tran_history.shape[0] == 0):
            return "No Data"

        max_account_value = tran_history[(tran_history['Account_Value'] == tran_history['Account_Value'].max())]
        if tran_history['Buy_Count'].sum() > 0:
            first_buy = tran_history[(tran_history['Buy_Count']>0)].index[0].strftime("%Y-%m-%d")
        else:
            first_buy = 'None'
        buys = len(tran_history[tran_history['Buy_Count']>0])
        sells = len(tran_history[tran_history['Sell_Count']>0])
        days_bought_or_sold = tran_history[(tran_history['Buy_Count'] > 0) | (tran_history['Sell_Count'] > 0)]

        # If no transactions, exit now else show transaction table
        if buys == 0 :
            return "No Data"
        
        output = f'<h2 style="text-decoration: underline;">Results of Backtesting for {stock}</h2><b>'
        output += "<ul>"
        output += f"First Buy On: {first_buy}<br>"
        output += f"Number of Buy Transactions : {buys}<br>"
        output += f"Number of Sell Transactions : {sells}<br>"
        output += f"Number of Days Transactions Happened : {len(days_bought_or_sold)} out of {len(tran_history)} Trading Days<br><br>"

        trans_from_first_buy = tran_history.loc[first_buy:]
        lowest_account_value = trans_from_first_buy[(trans_from_first_buy['Account_Value'] == trans_from_first_buy['Account_Value'].min())]
        max_drawdown = tran_history[(tran_history['ROI_pcnt'] == tran_history['ROI_pcnt'].min())]
        highest_ROI = tran_history[(tran_history['ROI_pcnt'] == tran_history['ROI_pcnt'].max())]

        output += f"Peak Account Value was on {max_account_value.index[0].strftime('%Y-%m-%d')} : ${max_account_value.iloc[0].Account_Value}<br>"
        output += f"Lowest Account Value was on {lowest_account_value.index[0].strftime('%Y-%m-%d')} : ${lowest_account_value.iloc[0].Account_Value}<br>"

        output += f"Highest ROI (Max % Return) was on {highest_ROI.index[0].strftime('%Y-%m-%d')} : {highest_ROI.iloc[0].ROI_pcnt}%<br>"
        output += f"Lowest ROI (Max % Drawdown) was on {max_drawdown.index[0].strftime('%Y-%m-%d')} : {max_drawdown.iloc[0].ROI_pcnt}%<br>"
        output += "</ul><hr>"

        return output

if __name__ == "__main__":
    # pass
    in_stock = input("Enter stock symbol : ").strip().upper()
    instock_list = [in_stock]
    
    # Define dates and corresponding buy signals (True/False)

    # Download End-of-day stock prices from Yahoo Finance API
    import yfinance as yf
    
    # Set the starting stock market date
    start_date = '2024-04-08'
    
    # Download the prices
    # df_prices = yf.download(in_stock,start=start_date,interval='1d',progress=False)
    df_prices = yf.Ticker(in_stock).history(start=start_date,interval='1d',period='max')
    df_prices.index = pd.to_datetime(df_prices.index).tz_localize(None)
    
    
    # Create a dictionary with dates as keys and buy signals as values
    dates = df_prices.index
    buy_signals = {date: 0 for date in df_prices.index} 
    
    # Create a prediction dataframe combining the price with the signals
    df_pred = pd.DataFrame(buy_signals.items(), columns=['Date', 'Predicted'])
    df_pred.set_index('Date', inplace=True)
    
    end_date = datetime.today().strftime('%Y-%m-%d')

    # Generate the date range
    date_range = pd.date_range(start=start_date, end=end_date)
    # Set the value for the 'Predicted' column
    df_pred['Predicted'] = 1
    df_pred = df_pred.shift(1).fillna(0)
    
    # Sample signals dataframe 
    # df_pred.loc['2024-04-09','Predicted']=1 # Buy
    df_pred.loc['2024-04-11','Predicted']=0 # Buy
    df_pred.loc['2024-04-12','Predicted']=0 # Buy
    df_pred.loc['2024-04-15','Predicted']=0 # Buy
    df_pred.loc['2024-04-16','Predicted']=0 # Buy
    df_pred.loc['2024-04-17','Predicted']=0 # Buy
    df_pred.loc['2024-04-18','Predicted']=0 # Buy
    # df_pred.loc['2024-04-25','Predicted']=0 # Buy
    df_pred.loc['2024-04-26','Predicted']=0 # Buy
    df_pred.loc['2024-04-29','Predicted']=0 # Buy
    df_pred.loc['2024-04-30','Predicted']=0 # Buy
    # df_pred.loc['2024-05-01','Predicted']=1 # Buy
    # df_pred.loc['2024-05-02','Predicted']=1 # Buy
    # df_pred.loc['2024-05-03','Predicted']=1 # Buy
    # df_pred.loc['2024-05-04','Predicted']=1 # Buy
    
    # Shift the Buy signals data by 1 day forward if the buying will happen the next day's open price
    # df_pred = df_pred.shift(1).fillna(0)
    
    print(df_pred)
    print(df_prices)
    
    # Run backtesting on the model to verify the results
    backtest = SignalsBacktester(df_in=df_prices, signals=df_pred, start_date=start_date, end_date=None, amount=10000)
    backtest.run_html()
    tran_history = backtest.get_tran_history()
    print(tran_history)
    backtest.results()
    matplotlib.use('GTK3Agg') 
    backtest.plot_account_image(f"{in_stock} Backtest since {start_date}",show_image=True)
