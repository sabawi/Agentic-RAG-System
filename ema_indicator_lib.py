#!/usr/bin/env python
# coding: utf-8

# In[40]:


import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 

# plt.style.use('fivethirtyeight')
# plt.rcParams['figure.figsize'] = (20,10)


# In[41]:


def generate_signals(data,fast_ema=5,slow_ema=13):
    data[f'{fast_ema}_day_EMA'] = data['Close'].ewm(span=fast_ema, adjust=False).mean()
    data[f'{slow_ema}_day_EMA'] = data['Close'].ewm(span=slow_ema, adjust=False).mean()
    data['signal'] = 0.0

    for i in range(len(data) - 1):
        if data.loc[data.index[i + 1], f'{fast_ema}_day_EMA'] > data.loc[data.index[i + 1], f'{slow_ema}_day_EMA'] and data.loc[data.index[i], f'{fast_ema}_day_EMA'] <= data.loc[data.index[i], f'{slow_ema}_day_EMA']:
            data.loc[data.index[i + 1], 'signal'] = 1
        elif data.loc[data.index[i + 1], f'{fast_ema}_day_EMA'] < data.loc[data.index[i + 1], f'{slow_ema}_day_EMA'] and data.loc[data.index[i], f'{fast_ema}_day_EMA'] >= data.loc[data.index[i], f'{slow_ema}_day_EMA']:
            data.loc[data.index[i + 1], 'signal'] = -1

    return data


# In[42]:


def implement_signal_strategy(prices, st):
    buy_price = []
    sell_price = []
    st_signal = []
    signal = 0
    
    for i in range(len(st)):
        if st.iloc[i-1] > prices.iloc[i-1] and st.iloc[i] < prices.iloc[i]:
            if signal != 1:
                buy_price.append(prices[i])
                sell_price.append(np.nan)
                signal = 1
                st_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                st_signal.append(0)
        elif st.iloc[i-1] < prices.iloc[i-1] and st.iloc[i] > prices.iloc[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices[i])
                signal = -1
                st_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                st_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            st_signal.append(0)
            
    return buy_price, sell_price, st_signal

if __name__ == "__main__":
    print("Plot Exponential Moving Average for a Stock:")
    print("============================================")
    stock = str(input("Enter Stock Symbol : ")).upper()
    fast_ema = int(input("Enter the Fast (Short Period) : "))
    slow_ema = int(input("Enter the Slow (Long Period) : "))
    start_date = input("Enter start Date (YYYY-MM-DD) :")
    # Download stock daily data
    data = yf.download(stock, start=start_date, interval='1d',progress=False)

    # Generate buy and sell signals
    stock_data = generate_signals(data,fast_ema=fast_ema,slow_ema=slow_ema)
    buy_price, sell_price, st_signal = implement_signal_strategy(stock_data['Close'], stock_data['signal'])

    print(stock_data)

    stock_data_noindex = stock_data.reset_index().copy()
    buy_price_list = [(stock_data_noindex.iloc[i]['Date'],stock_data_noindex.iloc[i]['Close'])  for i in range(len(stock_data_noindex)) if stock_data_noindex.iloc[i].signal == 1 ]
    sell_price_list = [(stock_data_noindex.iloc[i]['Date'],stock_data_noindex.iloc[i]['Close'])  for i in range(len(stock_data_noindex)) if stock_data_noindex.iloc[i].signal == -1 ]
    buy_price_df = pd.DataFrame(buy_price_list,columns=['Date','buyprice']).set_index('Date')
    sell_price_df = pd.DataFrame(sell_price_list,columns=['Date','sellprice']).set_index('Date')
    stock_data['buyprice'] = buy_price_df['buyprice']
    stock_data['sellprice'] = sell_price_df['sellprice']

    print("Signals Table:")
    print(stock_data[stock_data['signal']!=0][['signal','buyprice','sellprice']])

    print(f"Buy when Fast EMA({fast_ema}) CROSSES ABOVE the Slow EMA({slow_ema}))")
    print(f"Sell when Fast EMA({fast_ema}) CROSSES BLOW the Slow EMA({slow_ema}))")


    plot_data = stock_data.iloc[-1000:].copy()
    ax = plt.plot(plot_data['Close'], linewidth = 2)
    plt.plot(plot_data[f'{fast_ema}_day_EMA'],linewidth = 2,c='red')
    plt.plot(plot_data[f'{slow_ema}_day_EMA'],linewidth = 2,c='green')

    # plt.plot(plot_data['signal'], color = 'green', linewidth = 2, label = 'ST UPTREND')
    # plt.plot(stock_data['st_dt'], color = 'r', linewidth = 2, label = 'ST DOWNTREND')
    plt.plot(plot_data.index, plot_data['buyprice'], marker = '^', color = 'green', markersize = 12, linewidth = 0, label = 'BUY SIGNAL')

    plt.plot(plot_data.index, plot_data['sellprice'], marker = 'v', color = 'r', markersize = 12, linewidth = 0, label = 'SELL SIGNAL')
    plt.title(stock+' EMA CROSSINGS TRADING SIGNALS')
    plt.legend(['Close', f'{fast_ema}_day_EMA', f'{slow_ema}_day_EMA','Buy Signal','Sell Signal'],loc='upper left')
    plt.show()




