import sqlite3
from datetime import date, datetime
import pandas as pd
from tabulate import tabulate
from Backtester import SignalsBacktester as bt
import yfinance as yf
import warnings
from functools import wraps
import pymysql
import matplotlib
# matplotlib.use('TkAgg')  # Use an interactive backend
# plt.style.use('fivethirtyeight')
# plt.rcParams['figure.figsize'] = (20,10)


transact_record = []


def suppress_warnings(func):
    """Decorator to suppress warnings within a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            return func(*args, **kwargs)
    return wrapper


def add_data(data, date, symbols):
    """
    Adds a new entry to the provided data dictionary with the date and stock symbols set.
    If the date already exists, it appends the new symbols to the existing set.

    Args:
        data: A dictionary to store date and stock symbol sets.
        date: The date as a string in YYYY-MM-DD format.
        symbols: A list of stock symbols.
    """
    if date not in data:
        data[date] = {symbols}
    else:
        data[date].update({symbols})  # Update with new symbols using set(symbols)


def make_buys_df(data):
    """
    Converts the provided data dictionary to a Pandas DataFrame with columns 'Date' and 'Stock'.

    Args:
        data: A dictionary containing date and stock symbol sets.

    Returns:
        A Pandas DataFrame.
    """
    if not data:
        df = pd.DataFrame(columns=['Date', 'Stock'])  # Return empty DataFrame
        df = df.set_index('Date')
    else:
        # print(data)
        df = pd.DataFrame(data)
        
    return df

def get_filter_rows():
    rows = [
        {'FilterName': 'all_stocks', 'Description': 'All Stocks in Database', 'Comments': 'All the stocks being analyzed and screened in the database'},
        {'FilterName': 'gpt4o_sorting_recommendations', 'Description': 'Using GPT4o sorting for top picks', 'Comments': 'Based on which criteria fits a 6m to 1yr investment'},
        {'FilterName': 'confirmed_up_tred_buys', 'Description': 'Confirmed UpTrend BUYS', 'Comments': 'Confirmed Momentum Indicators'},
        {'FilterName': 'confirmed_up_trend_buys_NoST', 'Description': 'Confirmed UpTrend BUYS No Supertrend', 'Comments': 'Confirmed Momentum Indicators No Suoertrend'},
        {'FilterName': 'confirmed_signal_only', 'Description': 'Confirmed Signal Stocks ONLY', 'Comments': 'Only Confirmed Momentum Indicators'},
        {'FilterName': 'buybuybuy', 'Description': 'BUYS, BUYS, and more BUYS', 'Comments': 'All indicators are BUY and in supertrend'},
        {'FilterName': 'buybuybuy_not_st', 'Description': 'BUYS, BUYS, and more BUYS (Not necessarily ST winners)', 'Comments': 'All indicators are BUY but NOT in supertrend'},
        {'FilterName': 'all_up_safe', 'Description': 'All Roads Lead to UP & Safe', 'Comments': 'Restricts the BUY BUY BUY list to low risk stocks only'},
        {'FilterName': 'smx_st_win', 'Description': 'SMA Crossed and in Supertrend & Winner', 'Comments': 'Fast SMA Crossed up the Slow SMA, Supertrending and a Trend Winner'},
        {'FilterName': 'smx_ema_buys', 'Description': 'SMA Crossed and EMA Trend are Buys', 'Comments': 'Fast SMA Crossed up the Slow SMA, EMA Trend are both Buys'}
    ]
    
    return rows


# Example usage
# data = {}
# add_data(data, "2024-04-12", ["GOOG", "IBM"])
# add_data(data, "2024-04-15", ["AAPL", "MSFT"])
# add_data(data.copy(), "2024-04-12", ["AAPL"])  # Avoid modifying original data

# Create the DataFrame with a copy to prevent unintended modification
# df = create_dataframe(data.copy())

# print(df)

class TradeRecord:
    def __init__(self, transact, date, stock, note):
        self.transact = transact
        self.date = date
        self.stock = stock
        self.note = note

        # Validation logic can be added here
        if self.transact not in ('Buy', 'Sell', 'None'):
            raise ValueError(f"Invalid transaction type: {self.transact}")
        def __str__(self):
            # Return a string representation of the record data
            return f"Transact: {self.transact}, Date: {self.date}, Stock: {self.stock}, Note: {self.note}"

def transact(action,date,stock,note):
    # Create a TradeRecord object
    record = TradeRecord(action, date, stock, note)

    # Append the record to the data list
    transact_record.append(record)
    

def connect_db(host='localhost', user='root', password='Down2earth!', database='mystocks'):
    """Connects to the MySQL database and returns the connection object.

    Args:
        host (str): The hostname or IP address of the MySQL server.
        user (str): The username to use when connecting to the database.
        password (str): The password to use when connecting to the database.
        database (str): The name of the database to connect to.

    Returns:
        pymysql.Connection: The connection object to the database.
    """
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    return conn
    
def connect_db_old(db_file):
    """Connects to the database file and returns the connection object.

    Args:
        db_file (str): Path to the database file.

    Returns:
        sqlite3.Connection: The connection object to the database.
    """
    conn = sqlite3.connect(db_file)
    return conn

def query_data(conn, sql_statement):
    """Executes the provided SQL statement and returns the cursor object.

    Args:
        conn (sqlite3.Connection): The connection object to the database.
        sql_statement (str): The SQL statement to be executed.

    Returns:
        sqlite3.Cursor: The cursor object containing the results of the query.
    """
    cursor = conn.cursor()
    cursor.execute(sql_statement)
    return cursor

def process_data(cursor,conn ,filter_name = None):
    """Processes the data from the cursor and prints buy/sell alerts.

    This function iterates through the cursor data (assumed to be stock information with 
    "Last Run", "Stock", and "Last Price" columns) and simulates a trading process based on 
    specific conditions. It keeps track of a current portfolio and prints buy/sell alerts 
    as dates change and stock presence/absence changes.

    Args:
        cursor (sqlite3.Cursor): The cursor object containing the stock data.
    """
    current_portfolio = {}  # Use a dictionary to store stock symbols with last_run dates
    today_portfolio = {}
    sell_portfolio = {}
    
    # init processing_date to sometime in the far past
    processing_date = datetime.strptime("2000-01-01", "%Y-%m-%d")
    # init filtered_list_date to sometime in the far part
    filtered_list_date = processing_date
    
    for row in cursor.fetchall():
        last_run, stock, last_price = row
        date_last_run =  datetime.strptime(last_run, "%Y-%m-%d")
        stock = stock.strip().upper()
        # print(f"fetchall() Stock = {stock}, row={row}")
        
        # init the in_filtered_list flag for each new row
        in_filtered_list = False
        
        # Check if it's a new date
        # if date_last_run > processing_date : 
        if True:
            
            # print(f"************************* Stock = {stock}")
            # Get the recommendation list on this date for the given filter
            if date_last_run > filtered_list_date:
                # print(f"1 - Calling filter_list() {filter_name}")
                filtered_list = filter_list(last_run, filter_name, conn)
                # print('filtered_list:')
                # print(filtered_list)
                filtered_list_date = date_last_run
            
            # print(f"Stock = {stock}, set = {set(filtered_list['Stock'])}")
            if stock in set(filtered_list['Stock']):
                in_filtered_list = True
            
            # print(f"in_filtered_list = {in_filtered_list}")
            
            # If there are stocks to sell from the last pass, sell them now
            for sell_stock in sell_portfolio:
                # if sell_stock == 'MU':
                #     print(f"SELL: {sell_stock} on {processing_date}")
                    
                # Create a TradeRecord object
                transact("Sell", processing_date, sell_stock, "Sell at the next open")          
            
            current_portfolio = today_portfolio.copy()
            today_portfolio = {}
            
            # At this point, current_portfolio comes from the previous date's list (processing_date)
            # print("************************************************************")
            # print(f"Portfolio for ({processing_date}) Should be : {current_portfolio}")   
            # print("************************************************************")


            # update the processing_date to the one in the last record
            processing_date = date_last_run
            # print(f"New Date: {processing_date}")
            sell_portfolio = {}
            today_portfolio = {}            
            
            # Check if the stock in the record is in the current portfolio
            # If not transact a Buy and add it to today_portfolio
            if in_filtered_list and stock not in current_portfolio:    
                # if stock == 'MU':             
                #     print(f"BUY: {stock} on {last_run} at ${last_price}")         
                
                # Create a TradeRecord object
                transact("Buy", processing_date, stock, "Buy at the next open")   
                
                today_portfolio[stock] = last_run
        # Else the new record is still in the same date as the last pass
        # else:
        #     # Get the recommendation list on this date for the given filter
        #     if date_last_run > filtered_list_date:
        #         # print("2 - Calling filter_list()")
        #         filtered_list = filter_list(last_run, filter_name, conn)
        #         filtered_list_date = date_last_run
                
        #     # if the new record has a stock not in the current portfolio, buy it
        #     if in_filtered_list and stock not in set(current_portfolio):
        #         # print(f"BUY: {stock} on {last_run} at ${last_price}")                          
        #         # Create a TradeRecord object
                
        #         transact("Buy", processing_date, stock, "Buy at the next open")
                
        #     today_portfolio[stock] = last_run
            
        # print(f"current_portfolio = {current_portfolio}\ntoday_portfolio={today_portfolio} ")
        sell_portfolio = set(current_portfolio) - set(today_portfolio)

    # If there are stocks to sell from the last pass, sell them now
    # for sell_stock in sell_portfolio:
        # print(f"SELL: {sell_stock} on {processing_date}")
            
        # Create a TradeRecord object
        # transact("Sell", processing_date, sell_stock, "Sell at the next open")          
            
    # print("\n************************************************************")
    # print(f"FINAL Portfolio : {today_portfolio}")   
    # print("************************************************************")
                    
import pandas as pd
from datetime import datetime

def process_df_data(buy_eval_df):
    """Processes the data from the DataFrame and prints buy/sell alerts.

    This function iterates through the DataFrame data (assumed to be stock information with 
    "Last Run", "Stock", and "Last Price" columns) and simulates a trading process based on 
    specific conditions. It keeps track of a current portfolio and prints buy/sell alerts 
    as dates change and stock presence/absence changes.

    Args:
        buy_eval_df (pd.DataFrame): The DataFrame containing the stock data.
    """
    current_portfolio = {}  # Use a dictionary to store stock symbols with last_run dates
    today_portfolio = {}
    sell_portfolio = {}
    
    processing_date = datetime.strptime("2000-01-01", "%Y-%m-%d")
    
    for _, row in buy_eval_df.iterrows():
        last_run, stock, last_price = row["Last_Run"], row["Stock"], row["Last_Price"]
        date_last_run = datetime.strptime(last_run, "%Y-%m-%d")
        stock = stock.strip()
        
        # Check if it's a new date
        if date_last_run > processing_date: 
            # If there are stocks to sell from the last pass, sell them now
            for sell_stock in sell_portfolio:
                # print(f"SELL: {sell_stock} on {processing_date}")
                # Create a TradeRecord object
                transact("Sell", processing_date, sell_stock, "Sell at the next open")
            
            current_portfolio = today_portfolio.copy()
            today_portfolio = {}
            
            # At this point, current_portfolio comes from the previous date's list (processing_date)
            # print("************************************************************")
            # print(f"Portfolio for ({processing_date}) Should be : {current_portfolio}")   
            # print("************************************************************")
            
            # Update the processing_date to the one in the last record
            processing_date = date_last_run
            # print(f"New Date: {processing_date}")
            sell_portfolio = {}
            today_portfolio = {}
            
            # Check if the stock in the record is in the current portfolio
            # If not, transact a Buy and add it to today_portfolio
            if stock not in current_portfolio:                 
                # print(f"BUY: {stock} on {last_run} at ${last_price}")
                # Create a TradeRecord object
                transact("Buy", processing_date, stock, "Buy at the next open")
            
            today_portfolio[stock] = last_run
        else:
            # Else the new record is still in the same date as the last pass
            if stock not in set(current_portfolio):
                # print(f"BUY: {stock} on {last_run} at ${last_price}")
                # Create a TradeRecord object
                transact("Buy", processing_date, stock, "Buy at the next open")
            
            today_portfolio[stock] = last_run
        
        sell_portfolio = set(current_portfolio) - set(today_portfolio)
    
    # If there are stocks to sell from the last pass, sell them now
    for sell_stock in sell_portfolio:
        # print(f"SELL: {sell_stock} on {processing_date}")
        # Create a TradeRecord object
        transact("Sell", processing_date, sell_stock, "Sell at the next open")
    
    print("\n************************************************************")
    print(f"FINAL Portfolio : {today_portfolio}")   
    print("************************************************************")


def query_distinct_dates(conn, table_name):
    """
    Queries a database table and returns distinct values in the specified date column, 
    ordered by date in ascending order.

    Args:
        conn (sqlite3.Connection): The connection object to the database.
        table_name (str): The name of the table to query.
        date_column (str): The name of the column containing date values.

    Returns:
        list: A list of distinct date strings ordered by date.
    """
    cursor = conn.cursor()

    # Use strftime('%Y-%m-%d') to format dates consistently for comparison
    # Adapt the format string if your dates are stored differently
    sql_statement = f"""
        SELECT DISTINCT "Last_Run" 
        FROM {table_name} 
        ORDER BY 'Last_Run' ASC;
    """

    cursor.execute(sql_statement)
    results = cursor.fetchall()
  
    # Extract only the date strings from the results
    distinct_dates = [row[0] for row in results]
    return distinct_dates

def get_eval_by_date_old(conn, datestr):
    """
    Queries the database for rows in the 'stock_data' table where the 'Last Run' 
    column matches the provided date string and returns a pandas DataFrame.

    Args:
        conn (sqlite3.Connection): The connection object to the database.
        datestr (str): The date string to filter by (format should match 'Last Run' column).

    Returns:
        pandas.DataFrame: A DataFrame containing the matching rows from the table, 
                            or an empty DataFrame if no data is found.
    """
    # db_file = "data.db"  # Replace with your actual database filename
    # conn2 = connect_db(db_file)
    cursor = conn.cursor()

    sql_statement = f"""
        SELECT * FROM stock_data 
        WHERE "Last_Run" = ?;
    """

    cursor.execute(sql_statement, (datestr,))  # Use tuple for parameter substitution
    results = cursor.fetchall()
    # print(f" get_eval_by_date() {results}")

    # Check if any results were found
    if results:
        # Convert results to a DataFrame using column names from cursor description
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
    else:
        # Return an empty DataFrame if no data is found
        df = pd.DataFrame()

    return df

def get_eval_by_date(conn, datestr):
    """
    Queries the database for rows in the 'stock_data' table where the 'Last Run' 
    column matches the provided date string and returns a pandas DataFrame.

    Args:
        conn (pymysql.Connection): The connection object to the database.
        datestr (str): The date string to filter by (format should match 'Last Run' column).

    Returns:
        pandas.DataFrame: A DataFrame containing the matching rows from the table, 
                          or an empty DataFrame if no data is found.
    """
    cursor = conn.cursor()

    sql_statement = """
        SELECT * FROM stock_data 
        WHERE `Last_Run` = %s;
    """

    cursor.execute(sql_statement, (datestr,))  # Use tuple for parameter substitution
    results = cursor.fetchall()

    # Check if any results were found
    if results:
        # Convert results to a DataFrame using column names from cursor description
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
    else:
        # Return an empty DataFrame if no data is found
        df = pd.DataFrame()

    cursor.close()
    return df



def screen_for_buys(eval_df, ignore_supertrend_winners=False):
        if not ignore_supertrend_winners:
                buys_df = eval_df[ (eval_df['Supertrend_Winner']==True) &  
                        (eval_df['Supertrend_Result']=='Buy') & 
                        (eval_df['LR_Next_Day_Recomm'] == 'Buy,Buy,Buy') &
                        (eval_df['SMA_Crossed_Up']=='Buy')].sort_values(by=['Supertrend_Winner','Supertrend_Result',
                                                                            'ST_Signal_Date','SMA_Crossed_Up','SMA_X_Date'],
                                                                        ascending=[False,True,False,True,False])
        else:
                buys_df = eval_df[ (eval_df['Supertrend_Result']=='Buy') & 
                        (eval_df['LR_Next_Day_Recomm'] == 'Buy,Buy,Buy') &
                        (eval_df['SMA_Crossed_Up']=='Buy')].sort_values(by=['Supertrend_Winner','Supertrend_Result',
                                                                            'ST_Signal_Date','SMA_Crossed_Up','SMA_X_Date'],
                                                                        ascending=[False,True,False,True,False])            
        
        return buys_df
    
# def filter_list(datestr, filter_name, conn):
    
#     # print(f"in filter_list() datestr = {datestr}")
#     if not datestr:
#         datestr = date.today.today.strftime("%Y-%m-%d")
        
#     result = get_eval_by_date(conn, datestr)
#     if result.empty:
#         print(f"*** NO RESULTS on {datestr}")
#         return result
#     # else:
#     #     print("********* Results found **********")
        
#     # print(result)
#     match filter_name:
#         case "buybuybuy":
#             result = screen_for_buys(eval_df=result,ignore_supertrend_winners=False)
#             result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
#         case "buybuybuy_not_st":
#             result = screen_for_buys(eval_df=result,ignore_supertrend_winners=True)
#             result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
#         case "all_up_safe":
#             result = screen_for_buys(eval_df=result,ignore_supertrend_winners=False)
#             result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
#             result = result[(result['Beta']>0.8) & (result['Beta']<2) ].sort_values(by='SMA_X_Date', ascending=False).sort_values('Daily_VaR',ascending=False)
#         case "smx_st_win":
#             result = result[(result['SMA_Crossed_Up'] == 'Buy') & (result['Supertrend_Result'] == 'Buy') & (result['Supertrend_Winner'] == True) ].sort_values('SMA_X_Date', ascending=False)
#         case _:
#             print(f"No such pre-programmed filter '{filter_name}'")
            
            
#     return result


def filter_list(datestr, filter_name, conn):
    
    if not datestr:
        datestr = date.today.today.strftime("%Y-%m-%d")
        
    result = get_eval_by_date(conn, datestr)
    if result.empty:
        result = f"*** NO RESULTS on {datestr}"
        return result
        
    match filter_name:
        case "all_stocks":
            result = result.sort_values('Stock',ascending=True)
        case "gpt4o_sorting_recommendations":
            result = result[(result['Mom_Days_Confirmed']>=1) & (result['SMA_Crossed_Up'] == 'Buy')]
            result = result.sort_values(by=['Sharpe_Ratio%', 'CAPM', 'Momentum', 'Std._Dev.%', 'Supertrend_Result', 'SMA_Crossed_Up', 'EMA_Trend', 'Beta', 'Daily_VaR'], 
                            ascending=[False, False, False, True, False, False, False, False, True])
        case "confirmed_up_tred_buys":
            result = screen_for_buys(eval_df=result,ignore_supertrend_winners=False)
            result = result[(result['SMA_Crossed_Up'] == 'Buy') & (result['EMA_Trend'] == 'Buy') & (result['Confirmation'] == 'Buy') ].sort_values('Mom_Days_Confirmed', ascending=True)
            result = result[(result['Beta']>0.8) & (result['Beta']<2) ]
        case "confirmed_up_trend_buys_NoST":
            result = screen_for_buys(eval_df=result, ignore_supertrend_winners=True)
            result = result[(result['SMA_Crossed_Up'] == 'Buy') & (result['EMA_Trend'] == 'Buy') & (result['Confirmation'] == 'Buy') ].sort_values('Mom_Days_Confirmed', ascending=True)
            # result = result[(result['Beta']>0.8) & (result['Beta']<2) ]            
        case "confirmed_signal_only":
            result = result[ (result['Confirmation'] == 'Buy') ].sort_values(by=['Mom_Days_Confirmed'], ascending=[True])
        case "buybuybuy":
            result = screen_for_buys(eval_df=result,ignore_supertrend_winners=False)
            result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
        case "buybuybuy_not_st":
            result = screen_for_buys(eval_df=result,ignore_supertrend_winners=True)
            result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
        case "all_up_safe":
            result = screen_for_buys(eval_df=result,ignore_supertrend_winners=False)
            result = result.sort_values('Daily_VaR',ascending=False).sort_values('Sharpe_Ratio%',ascending=True).sort_values(by='SMA_X_Date', ascending=False)
            result = result[(result['Beta']>0.8) & (result['Beta']<2) ].sort_values(by='SMA_X_Date', ascending=False).sort_values('Daily_VaR',ascending=False)
        case "smx_st_win":
            result = result[(result['SMA_Crossed_Up'] == 'Buy') & (result['Supertrend_Result'] == 'Buy') & (result['Supertrend_Winner'] == True) ].sort_values('SMA_X_Date', ascending=False)
        case "smx_ema_buys":
            result = result[(result['SMA_Crossed_Up'] == 'Buy') & (result['EMA_Trend'] == 'Buy') ].sort_values('EMA_Days_at_Buy', ascending=True)
        case _:
            result = f"No such pre-programmed filter '{filter_name}'"
            
            
    return result


def get_user_inputs():
    """
    Prompts the user for market date and recommendation list name.

    Returns:
        tuple: A tuple containing the market date (string) and recommendation list name (string).
    """

    while True:
        # Get market date (loop until valid format)
        market_date = input("Enter market date (YYYY-MM-DD): ")
        try:
            # Check if date format is valid (YYYY-MM-DD)
            datetime.strptime(market_date, "%Y-%m-%d")
            break  # Exit loop if format is valid
        except ValueError:
            print("Invalid market date format. Please use YYYY-MM-DD.")

    # Get recommendation list name (no spaces allowed)
    while True:
        recommendation_list_name = input("Enter recommendation list name (no spaces): ")
        if not recommendation_list_name.isspace():  # Check for any spaces
            break  # Exit loop if no spaces
        else:
            print("Recommendation list name cannot contain spaces.")

    return market_date, recommendation_list_name

def report_buy_sell_backtest(inDate, recommendation_filter, stock, is_plot):
    db_file = "data.db"  # Replace with your actual database filename
    # conn = connect_db(db_file)
    conn = connect_db()
    output = "<div id='backtesting_results'>"
    data = {}
    invest_amount =10000 # Initial investment in $$
    
    # Define column names and data types
    # filter_columns = ['FilterName', 'Description', 'Comments']
    # fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
    
    
    # # Create an empty DataFrame with specified structure
    # filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
    
    # Define a list of dictionaries, where each dictionary represents a row
    # rows = [
    #     {'FilterName': 'buybuybuy', 'Description': 'BUYS, BUYS, and more BUYS', 'Comments': 'All indicators are BUY and in supertrend'},
    #     {'FilterName': 'buybuybuy_not_st', 'Description': 'BUYS, BUYS, and more BUYS (Not necessarily ST winners)', 'Comments': 'All indicators are BUY but NOT in supertrend'},
    #     {'FilterName': 'all_up_safe', 'Description': 'All Roads Lead to UP & Safe', 'Comments': 'Restricts the BUY BUY BUY list to low risk stocks only'},
    #     {'FilterName': 'smx_st_win', 'Description': 'SMA Crossed and in Supertrend & Winner', 'Comments': 'Fast SMA Crossed up the Slow SMA, Supertrending and a Trend Winner'}
    # ]

    rows = get_filter_rows()
    
    # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
    filters_df = pd.DataFrame([row for row in rows])

    # print(f"{recommendation_filter} \n {filters_df['FilterName']}")
    if recommendation_filter in set(filters_df['FilterName']):
        matching_row = next((row for row in rows if row['FilterName'] == recommendation_filter), None)
        # output +=(f"\n{matching_row['Description']}<br>")
        # output +=("=========================<br>")
        buys_eval_df = filter_list(datestr=inDate,filter_name=recommendation_filter,conn=conn)
        # output +=(f"{len(buys_eval_df)} Stocks:<br>")
        if not buys_eval_df.empty:
            sublist = ','.join(buys_eval_df['Stock'].astype(str))
            # output +=(sublist)+"<br>"
            # output +=buys_eval_df.to_html()
        
        output += f"<h4>Applied Strategy : {matching_row['Description']}</hr>"
        # +filters_df[filters_df['FilterName'] == recommendation_filter]['Description']
    else:
        output += ("Filter NOT found<br>")
    
    sql_statement = f"""
        select Last_Run, Stock , Last_Price 
        from stock_data 
        where Last_Run >= {inDate}
        ORDER BY Last_Run;
        """
    cursor = query_data(conn, sql_statement)
    process_data(cursor,conn=conn,filter_name=recommendation_filter)
    conn.close()
    
    # Print the data structure (accessing record fields using dot notation)
    for record in transact_record:
        add_data(data,record.date,f"{record.stock}")

    records = []
    for record in transact_record:
        record_dict = {
            'Transact': record.transact,
            'Date': record.date,  # Assuming date is already a datetime object
            'Stock': record.stock,
            'Note': record.note
        }
        records.append(record_dict)

    # Convert dictionary to list of records (tuples)
    items = [(date, list(symbols)) for date, symbols in data.items()]
    buy_stocks_df = pd.DataFrame(items,columns=['Date','Stock'])
    buy_stocks_df = buy_stocks_df.set_index('Date')
    # print(buy_stocks_df)

    # Create a Series with 0s (assuming all dates initially don't have the stock)
    # buy_alerts = pd.Series(0, index=buy_stocks_df.index)

    # start_date = buy_alerts.index[0]
    start_date = inDate 
    # print(f"Alert start Date {start_date}")
    # df_prices = yf.download(stock,start=start_date,interval='1d',period='max',progress=False)
    df_prices = yf.Ticker(stock).history(start=start_date,interval='1d',period='max')
    df_prices.index = pd.to_datetime(df_prices.index).tz_localize(None)
    
    # Create a Series with 0s (assuming all dates initially don't have the stock)
    buy_alerts = pd.Series(0, index=df_prices.index)
    
    
    for i, row in buy_stocks_df.iterrows():
        # print(i,row["Stock"])
        if stock in row['Stock']:
            buy_alerts.loc[i] = 1
            
    # buy_alerts_original = buy_alerts.copy()
    # print("Before Shift :",buy_alerts)
    buy_alerts = buy_alerts.shift(1).fillna(0)
    # print("After Shift :",buy_alerts)
    
    # print("Buy Alerts ",buy_alerts)
    df_pred = pd.DataFrame(buy_alerts,columns=['Predicted'],index=df_prices.index)
    # print("Predicted  :",df_pred)


    # Run backtesting on the model to verify the results
    backtest = bt(df_in=df_prices, signals=df_pred, start_date=start_date, end_date=None, amount=invest_amount)
    output += backtest.run_html(stock)
    tran_history = backtest.get_tran_history()
    
    # print(tran_history)
    output += backtest.results_html(stock)
    
    # plot_image = backtest.plot_account_image(f"{stock} Backtest since {start_date}")
    # img_data = plot_image.getvalue()
    
    output += f'<h2 style="text-decoration: underline;">Backtesting Transaction History for {stock}</h2><b>'
    output += tran_history.to_html(classes='table table-bordered', border=0, index=True, table_id='tran-history-table')
    output += f'<br><br>'
    output += "</div>"
    if is_plot == 0:
        return output
    elif is_plot == 1:
        plot_image = backtest.plot_account_image(f"{stock} Backtest ${invest_amount} starting {start_date}")
        return plot_image
    
def plot_account_image_route(inDate, recommendation_filter, stock):
    # print(f"In plot_account_image {inDate}, {recommendation_filter}, {stock}")
    db_file = "data.db"  # Replace with your actual database filename
    conn = connect_db(db_file)
    data = {}
    
    # Go back 100 days
    inDate = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=100)).strftime("%Y-%m-%d")
    
    # Define column names and data types
    filter_columns = ['FilterName', 'Description', 'Comments']
    fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
    
    
    # Create an empty DataFrame with specified structure
    filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
    
    # Define a list of dictionaries, where each dictionary represents a row
    rows = [
        {'FilterName': 'buybuybuy', 'Description': 'BUYS, BUYS, and more BUYS', 'Comments': 'All indicators are BUY and in supertrend'},
        {'FilterName': 'buybuybuy_not_st', 'Description': 'BUYS, BUYS, and more BUYS (Not necessarily ST winners)', 'Comments': 'All indicators are BUY but NOT in supertrend'},
        {'FilterName': 'all_up_safe', 'Description': 'All Roads Lead to UP & Safe', 'Comments': 'Restricts the BUY BUY BUY list to low risk stocks only'},
        {'FilterName': 'smx_st_win', 'Description': 'SMA Crossed and in Supertrend & Winner', 'Comments': 'Fast SMA Crossed up the Slow SMA, Supertrending and a Trend Winner'}
    ]

    # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
    filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)

    # print(f"{recommendation_filter} \n {filters_df['FilterName']}")
    if recommendation_filter in set(filters_df['FilterName']):
        matching_row = next((row for row in rows if row['FilterName'] == recommendation_filter), None)
        # output +=(f"\n{matching_row['Description']}<br>")
        # output +=("=========================<br>")
        buys_eval_df = filter_list(datestr=inDate,filter_name=recommendation_filter,conn=conn)
        # output +=(f"{len(buys_eval_df)} Stocks:<br>")
        if not buys_eval_df.empty:
            sublist = ','.join(buys_eval_df['Stock'].astype(str))
            # output +=(sublist)+"<br>"
            # output +=buys_eval_df.to_html()
        
    
    sql_statement = """
        select Last_Run, Stock , Last_Price 
        from stock_data 
        ORDER BY Last_Run;
        """
    cursor = query_data(conn, sql_statement)
    process_data(cursor,conn=conn,filter_name=recommendation_filter)
    conn.close()
    # print("transact_record:")
    # Print the data structure (accessing record fields using dot notation)
    for record in transact_record:
        add_data(data,record.date,f"{record.stock}")

    records = []
    for record in transact_record:
        record_dict = {
            'Transact': record.transact,
            'Date': record.date,  # Assuming date is already a datetime object
            'Stock': record.stock,
            'Note': record.note
        }
        # print(record_dict)
        records.append(record_dict)

    # Convert dictionary to list of records (tuples)
    items = [(date, list(symbols)) for date, symbols in data.items()]
    buy_stocks_df = pd.DataFrame(items,columns=['Date','Stock'])
    buy_stocks_df = buy_stocks_df.set_index('Date')

    # Create a Series with 0s (assuming all dates initially don't have the stock)
    buy_alerts = pd.Series(0, index=buy_stocks_df.index)

    # start_date = buy_alerts.index[0]
    start_date = inDate 
    # print(f"Alert start Date {start_date}")
    # df_prices = yf.download(stock,start=start_date,interval='1d',period='max',progress=False)
    df_prices = yf.Ticker(stock).history(start=start_date,interval='1d',period='max')
    
    # print(df_prices)
    
    for i, row in buy_stocks_df.iterrows():
        # print(i,row["Stock"])
        if stock in row['Stock']:
            buy_alerts.loc[i] = 1
            
    # buy_alerts_original = buy_alerts.copy()
    
    print("Before Shift :",buy_alerts)
    buy_alerts = buy_alerts.shift(1).fillna(0)
    print("After Shift :",buy_alerts)
    
    # print("Buy Alerts ",buy_alerts)
    df_pred = pd.DataFrame(buy_alerts,columns=['Predicted'],index=df_prices.index)

    # Run backtesting on the model to verify the results
    # print(f"INPUT DATA: {df_prices}, {df_pred}, {start_date}")
    backtest = bt(df_in=df_prices, signals=df_pred, start_date=start_date, end_date=None, amount=10000)
    tran_history = backtest.get_tran_history()
    print(tran_history)
    
    plot_image = backtest.plot_account_image(f"{stock} Backtest since {start_date}")
    # print("Out of plot_account_image ")
    
    return plot_image
    
def get_filters_df():
    rows = get_filter_rows()

    # Define column names and data types
    filter_columns = ['FilterName', 'Description', 'Comments']
    fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}

    # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
    filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)
    
    return filters_df
    
def main():
    """Main function to connect, query, and process data"""
    db_file = "data.db"  # Replace with your actual database filename
    # conn = connect_db(db_file)
    conn = connect_db()

    data = {}

    # Define column names and data types
    filter_columns = ['FilterName', 'Description', 'Comments']
    fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
    
    
    # Create an empty DataFrame with specified structure
    filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
    
    # Define a list of dictionaries, where each dictionary represents a row
    # rows = [
    #     {'FilterName': 'buybuybuy', 'Description': 'BUYS, BUYS, and more BUYS', 'Comments': 'All indicators are BUY and in supertrend'},
    #     {'FilterName': 'buybuybuy_not_st', 'Description': 'BUYS, BUYS, and more BUYS (Not necessarily ST winners)', 'Comments': 'All indicators are BUY but NOT in supertrend'},
    #     {'FilterName': 'all_up_safe', 'Description': 'All Roads Lead to UP & Safe', 'Comments': 'Restricts the BUY BUY BUY list to low risk stocks only'},
    #     {'FilterName': 'smx_st_win', 'Description': 'SMA Crossed and in Supertrend & Winner', 'Comments': 'Fast SMA Crossed up the Slow SMA, Supertrending and a Trend Winner'}
    # ]

    rows = get_filter_rows()
    
    # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
    filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)

    # Print the formatted string to the command line
    print(filters_df)
    
    test_datestr, filter_name = get_user_inputs()

    print(f"{filter_name} \n {filters_df['FilterName']}")
    if filter_name in set(filters_df['FilterName']):
        matching_row = next((row for row in rows if row['FilterName'] == filter_name), None)
        print(f"\n{matching_row['Description']}")
        print("=========================")
        buys_eval_df = filter_list(datestr=test_datestr,filter_name=filter_name,conn=conn)
        print(f"{len(buys_eval_df)} Stocks:",flush=True)
        if not buys_eval_df.empty:
            sublist = ','.join(buys_eval_df['Stock'].astype(str))
            print(sublist,flush=True)
            print(buys_eval_df)
        
    else:
        print("Filter NOT found")
    
    sql_statement = """
        select Last_Run, Stock , Last_Price 
        from stock_data 
        ORDER BY Last_Run;
        """
    cursor = query_data(conn, sql_statement)
    process_data(cursor,conn=conn,filter_name=filter_name)
    conn.close()
    
    # Print the data structure (accessing record fields using dot notation)
    for record in transact_record:
        add_data(data,record.date,f"{record.stock}")

    records = []
    for record in transact_record:
        record_dict = {
            'Transact': record.transact,
            'Date': record.date,  # Assuming date is already a datetime object
            'Stock': record.stock,
            'Note': record.note
        }
        records.append(record_dict)

    # Assuming 'data' is the list of dictionaries from previous examples
    # transact_df = pd.DataFrame(records)
    # print(transact_df)
    # print(tabulate(transact_df[transact_df['Date']>=test_datestr], headers=transact_df.columns, tablefmt="grid"))
    
    # Convert dictionary to list of records (tuples)
    items = [(date, list(symbols)) for date, symbols in data.items()]
    buy_stocks_df = pd.DataFrame(items,columns=['Date','Stock'])
    buy_stocks_df = buy_stocks_df.set_index('Date')
    # print(buy_stocks_df)
    # Print the DataFrame
    # print(tabulate(buy_stocks_df[buy_stocks_df.index>=test_datestr], headers=buy_stocks_df.columns, tablefmt="grid"))


    in_stock = input("Enter stock symbol : ").strip().upper()
    # instock_list = [in_stock]
    # print("Target = ", instock_list)

    # print(tabulate(transact_df[(transact_df['Date']>=test_datestr) & (transact_df['Stock'] == in_stock)], headers=transact_df.columns, tablefmt="grid"))

    # Create a Series with 0s (assuming all dates initially don't have the stock)
    buy_alerts = pd.Series(0, index=buy_stocks_df.index)

    # start_date = buy_alerts.index[0]
    start_date = test_datestr 
    # print(f"Alert start Date {start_date}")
    # df_prices = yf.download(in_stock,start=start_date,interval='1d',period='max',progress=False)
    df_prices = yf.Ticker(in_stock).history(start=start_date,interval='1d',period='max')
    
    
    for i, row in buy_stocks_df.iterrows():
        # print(i,row["Stock"])
        if in_stock in row['Stock']:
            buy_alerts.loc[i] = 1
            
    # buy_alerts_original = buy_alerts.copy()
    # print("Before Shift :",buy_alerts,flush=True)
    buy_alerts = buy_alerts.shift(1).fillna(0)
    # print("After Shift :",buy_alerts,flush=True)
    
    # print("Buy Alerts ",buy_alerts)
    df_pred = pd.DataFrame(buy_alerts,columns=['Predicted'],index=df_prices.index)

    # Run backtesting on the model to verify the results
    backtest = bt(df_in=df_prices, signals=df_pred, start_date=start_date, end_date=None, amount=10000)
    backtest.run()
    tran_history = backtest.get_tran_history()
    # print(tran_history)
    backtest.results()
    backtest.plot_account_image(f"{in_stock} Backtest since {start_date}",show_image=True)

    # buy_alerts = buy_alerts.shift(1).fillna(0)
    # print(buy_alerts)
    
    # df_pred = pd.DataFrame(buy_alerts,columns=['Predicted'],index=df_lagged.index)

    # # Run backtesting on the model to verify the results
    # backtest = bt(df_in=df_in, signals=df_pred, start_date=start_date, end_date=None, amount=100000)
    # backtest.run()
    # tran_history = backtest.get_tran_history()
      
if __name__ == "__main__":
    main()
    # report_buy_sell_backtest("2024-04-03","all_up_safe","SPY")
