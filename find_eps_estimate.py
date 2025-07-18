import threading
from flask import Flask, request, send_file, jsonify, Response, stream_with_context
from flask_cors import CORS  # Import CORS
import json
import sqlite3
from datetime import date, datetime
import pandas as pd
from prettytable import PrettyTable
import io
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use a non-GUI backend
import buy_sell_signal_generator as signals
import ta_verifer as ta
from datetime import datetime, timedelta
import os
import signal
import subprocess
# import logging
import sys
import traceback
from io import StringIO

import pymysql

# # Global flag to control whether to overload print
# overload_print = True

# # Custom print function
# def my_print(*args, **kwargs):
#     if overload_print:
#         # Custom logic (e.g., prepend a timestamp)
#         import datetime
#         current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         builtins.print(f"{current_time} - ", *args, **kwargs)
#     else:
#         # Use the original built-in print function
#         builtins.print(*args, **kwargs)

# # Replace the built-in print function with the custom one
# import builtins
# builtins.print = my_print

# Set up logging
# logging.basicConfig(filename='server.log', level=logging.ERROR)
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
CORS(app, resources={r"/execute": {"origins": "http://192.168.1.58"}})

lock = threading.Lock()

if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20,10)


# Get the global filter list 
rows = signals.get_filter_rows()

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
        conn (pymysql.Connection): The connection object to the database.
        sql_statement (str): The SQL statement to be executed.

    Returns:
        pymysql.cursors.Cursor: The cursor object containing the results of the query.
    """
    cursor = conn.cursor()
    cursor.execute(sql_statement)
    return cursor


def get_eval_by_date_old(conn, datestr):
    """
    Queries the database for rows in the 'stock_data' table where the 'Last Run' 
    column matches the provided date string and returns a pandas DataFrame.

    Args:
        conn (sqlite3.Connection): The connection object to the database.
        datestr (str): The date string to filter by (format should match 'Last_Run' column).

    Returns:
        pandas.DataFrame: A DataFrame containing the matching rows from the table, 
                            or an empty DataFrame if no data is found.
    """
    cursor = conn.cursor()

    sql_statement = f"""
        SELECT * FROM stock_data 
        WHERE "Last_Run" = ?;
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

    return df


def make_text_clickable(in_df, column_name, linktext, replace_text):
    out_df = in_df.copy()
    # pd.options.mode.copy_on_write = True
    
    for index,row in in_df.iterrows():
        old_text = out_df.loc[index,column_name]
        new_text = linktext.replace(replace_text, old_text)
        new_text = f"<a href='{new_text}'  target='_blank' title='{old_text} External Link'>{old_text}</a>"
        out_df.loc[index,column_name] = new_text
        
    return out_df

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
    
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/execute', methods=['POST'])
def execute_code():
    code = request.form.get('code')
    
    # Debugging: Print the received code on the server side
    # print(f"Received code: {code}", file=sys.stdout)
    sys.stdout.flush()

    try:
        # Execute the code using subprocess (ensure Python 3 is used)
        exec_output = subprocess.run(
            ['python3', '-c', code], 
            capture_output=True, 
            text=True, 
            timeout=30  # Set a timeout for the execution to prevent hanging
        )

        # Print the output and error for debugging
        # print(f"Execution output: {exec_output.stdout}", file=sys.stdout)
        # print(f"Execution error: {exec_output.stderr}", file=sys.stderr)
        sys.stdout.flush()

        # Return the output and any errors
        return jsonify({
            'output': exec_output.stdout,
            'stderr': exec_output.stderr,
            'result': 'Execution completed'
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'output': '',
            'stderr': 'Execution timed out',
            'result': 'Timeout error'
        }), 504

    except Exception as e:
        # Catch other execution errors
        return jsonify({
            'output': '',
            'stderr': str(e),
            'result': 'Error during execution'
        }), 500


@app.route('/shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@app.route('/restart', methods=['POST'])
def restart_server():
    print("RESTARTIN ... ",flush=True)
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"message": "Server is restarting..."}), 200

@app.route('/urlproxy', methods=['POST'])
def urlproxy():
    
    row_data = request.data.decode("utf-8")
    
    data = json.loads(row_data)
    url = data['url']
    response = requests.get(url)
    return(response.content)
            

import fitz 
import io

@app.route("/retrieve_system_prompts", methods=['POST'])
def retrieve_system_prompts():
    data = request.get_json()
    
    filename = data.get('system_prompts_filename')
    print(filename,flush=True)
    if "system_prompts_filename" not in data:
        return jsonify({'message': 'Missing system_prompts_filename parameter'}), 400
    
    system_prompts_filename = data["system_prompts_filename"]
    print(f"----> {system_prompts_filename} from server",flush=True)
    
    if not system_prompts_filename:
        return jsonify({'message': 'system_prompts_filename cannot be empty'}), 400
    
    try:
        # Construct the full path to the file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prompts_dir = os.path.join(base_dir, 'prompts')
        file_path = os.path.join(prompts_dir, filename)

        # Print the directory being read from for debugging
        print(f"Reading file from: {file_path}",flush=True)

        # Read the file content
        with open(file_path, 'r') as file:
            file_content = file.read()

        # Return the file content as JSON
        # return jsonify({"system_prompts": file_content}), 200
        return jsonify(file_content), 200
    
    except FileNotFoundError:
        return jsonify({'message': f'File not found: {system_prompts_filename}'}), 404
    
    except Exception as e:
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500
        
        
    
    

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    # Check if a file part is present in the request
    if 'pdf' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['pdf']

    # If user does not select a file
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    try:   
        def extract_text_from_pdf(pdf_file):
            # Create a buffer to store the extracted text
            text_buffer = io.StringIO()

            with fitz.open(stream=pdf_file.read(), filetype="pdf") as pdf_document:
                # Iterate over each page and extract text
                for page_num in range(pdf_document.page_count):
                    page = pdf_document.load_page(page_num)
                    text = page.get_text("text")  # Extract text from the page
                    text_buffer.write(text)

            # Move the buffer cursor to the beginning
            text_buffer.seek(0)

            # Get the text content from the buffer as a string
            return text_buffer.getvalue()

        extracted_text = extract_text_from_pdf(file)
    
        return jsonify({'message': extracted_text})
    
    except Exception as e:
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500
        

@app.route('/plot_ema_trend', methods=['POST'])
def plot_ema_trend():
    with lock:
        data = request.get_json()
        stock = data['stock']
        start_date = data['start_date']
        fast=data['fast']
        slow=data['slow']
        lookback=data['lookback']
        
        year_back_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")
        two_weeks_back_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=100)).strftime("%Y-%m-%d")
    
        # print(stock,start_date,fast,slow,lookback)
        # print( f"Start Date : {two_weeks_back_start_date}")
        ret_data = ta.generate_pdta_plot_image(stock=stock,start_date=two_weeks_back_start_date,fast=fast,slow=slow,lookback=lookback)
        # print("plot_ema_trend PLOT")
        return send_file(ret_data, mimetype='image/png')

@app.route('/signals_backtest', methods=['POST'])
def signals_backtest():
    with lock:
        # Define column names and data types
        filter_columns = ['FilterName', 'Description', 'Comments']
        fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
        
        # Create an empty DataFrame with specified structure
        filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
        

        # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
        filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)    
        
        data = request.get_json()
        date = data['date']
        filter_name = filters_df.loc[int(data['filter'])]['FilterName']
        stock = data['stock']
        is_plot = data['is_plot']

        ret_data = signals.report_buy_sell_backtest(date, filter_name, stock, is_plot)
        # print(ret_data)
        if is_plot == 0:
            if ret_data == None:
                ret_data == "No Data"
                return jsonify({"error": str("No Image")}), 200
            else:
                return ret_data
        elif is_plot == 1:
            if ret_data == None:
                return jsonify({"error": str("No Image")}), 400
            else:
                # print("signals_backtest PLOT ")
                return send_file(ret_data, mimetype='image/png')

@app.route('/plot_account', methods=['POST'])
def plot_account():
    with lock:
        # Define column names and data types
        # print("from plot_account() Hello World")
        filter_columns = ['FilterName', 'Description', 'Comments']
        fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
        
        # Create an empty DataFrame with specified structure
        filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
        

        # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
        filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)    
        
        data = request.get_json()
        date = data['date']
        filter_name = filters_df.loc[int(data['filter'])]['FilterName']
        stock = data['stock']
        img = signals.plot_account_image_route(date, filter_name, stock)
        # print("Got Image")
        
        
            # Create a simple plot using Matplotlib
        # df = pd.DataFrame({
        #     'x': [1, 2, 3, 4, 5],
        #     'y': [10, 20, 25, 30, 35]
        # })

        # plt.figure()
        # plt.plot(df['x'], df['y'])
        # plt.title('Sample Plot')
        # plt.xlabel('X-axis')
        # plt.ylabel('Y-axis')

        # # Save the plot to a BytesIO object
        # img = io.BytesIO()
        # plt.savefig(img, format='png')
        # img.seek(0)  # Move to the beginning of the BytesIO object
        # plt.close()  # Close the plot to free up memory

        # Send the image as a response
        # return send_file(img, mimetype='image/png')

        
        
        # Return the image data as a response
        return send_file(img, mimetype='image/png')

@app.route('/get_rows', methods=['GET'])
def get_rows():
    return jsonify(rows)


@app.route('/find_eps_estimate', methods=['POST'])
def find_eps_estimate():
    with lock:
        date = request.form['date']

        db_file = "/home/sabawi/Development/stocks_evaluator/data.db"  # Replace with your actual database filename
        # conn = connect_db_old(db_file)
        conn = connect_db()
        
        data = {}
        
        # Define column names and data types
        filter_columns = ['FilterName', 'Description', 'Comments']
        fdata_types = {'FilterName': str, 'Description': str, 'Comments': str}
        
        # Create an empty DataFrame with specified structure
        filters_df = pd.DataFrame(columns=filter_columns, dtype=str)    
        

        # Efficiently populate the DataFrame using list comprehension and pd.DataFrame
        filters_df = pd.DataFrame([row for row in rows], columns=filter_columns)

        test_datestr = date
        # print("Request Form index =", request.form['filter'])

        filter_name= filters_df.loc[int(request.form['filter'])]['FilterName']
        # print(filter_name)
        table_text = ''
        jscript = """
        <script>
            $(document).ready( function () {
                $('#sortable-table').DataTable({"lengthMenu": [ [10, 25, 50, -1], [10, 25, 50, "All"] ], // Customize the options as needed
                    "pageLength": -1 // Change this number to set the initial number of rows displayed per page
                    });
            });
        </script>\n
        """
        output = jscript + f"Recommendation List Name : <b>{filter_name}</b> </br>"
        if filter_name in set(filters_df['FilterName']):
            matching_row = next((row for row in rows if row['FilterName'] == filter_name), None)
            output += f"\n<h2 style='text-decoration: underline;'>{matching_row['Description']}</br>"
            output += "</h2>"
            
            # Add a new column for each person's website
            def create_key_data_link(row):
                url = "http://sabawi2-lenovo-y50-70/cgi-bin/stockdata.py?stock=" + row['Stock'].lower()
                return f"<a href='{url}' target='_blank'>{row['Stock']}</a>"

            buys_eval_df = signals.filter_list(datestr=test_datestr,filter_name=filter_name,conn=conn)
            if type(buys_eval_df) == pd.core.frame.DataFrame:
                key_data = buys_eval_df.apply(create_key_data_link, axis=1)
            else:
                output += "No Data Available"
            
            if isinstance(buys_eval_df, pd.DataFrame):
                output +=f"{len(buys_eval_df)} Fidelity Pages:"
            if isinstance(buys_eval_df, pd.DataFrame) and not buys_eval_df.empty:
                
                linktext = "https://digital.fidelity.com/prgw/digital/research/quote/dashboard/summary?symbol=????"
                input_df1 = buys_eval_df.copy()
                input_df1 = make_text_clickable(input_df1,'Stock',linktext,'????')
                
                sublist = ', '.join(input_df1['Stock'].astype(str))
                output +=f"{sublist}</br><hr>"
                
                output +=f"{len(buys_eval_df)} Key Data:"
                sublist2 = ', '.join(key_data.astype(str))
                output +=f"{sublist2}</br><hr>"
                
                # output +=buys_eval_df.to_string()
                table = PrettyTable(buys_eval_df.columns.tolist())
                # Add rows to the table
                for _, row in buys_eval_df.iterrows():
                    table.add_row(row.tolist())

                # Generate the HTML table
                table_text = table.get_html_string()
                # Manually set the table ID to "sortable-table"
                table_text = table_text.replace("<table>", '<table id="sortable-table">')
                
                # Wrap the table with a div for DataTables
                output += f'\n<div class="dataTables_wrapper">\n{table_text}\n</div>\n</html>'
            else:
                table_text = buys_eval_df
        else:
            output +="Filter NOT found"
        
        return output

import requests
@app.route('/llama3_1b/prompt', methods=['POST'])
def llama3_1b_prompt():
    with lock:
        form = request.get_json()
        payload = {
            # "model": "llama3",
            "model": form["model"],
            "prompt": form['prompt'],
            "stream": form.get('stream', True)
        }
        response = requests.post('http://127.0.0.1:11434/api/generate', json=payload)
        # return jsonify(response.json())
        if payload['stream']:
            # print(f"Response Content: {response.content.decode('utf-8').response}")

            return Response(stream_with_context(response.iter_content()), content_type=response.headers['Content-Type'])
        else:
            return jsonify(response.json())

# ###############################################################################################################
# ###############################################################################################################
# The secret tools: It's purpose is to check and verify that the LLM is able to call tools 

import os
import wikipediaapi
import re
from typing import Dict, Any, Callable, List
import requests
import json
import yfinance as yf
from bs4 import BeautifulSoup
from gnews import GNews

# logger = logging.getLogger(__name__)

###################################################################################################################
############################################ Tools Functions ######################################################

def get_news_from_google(keyword ):
    """
    Retrieve news articles from Google News for a given keyword.

    Args:
        keyword (str): The search term or topic to fetch news about.

    Returns:
        str: A formatted string containing news article details, including:
            - Published date
            - Title
            - Description

        If an error occurs, returns a string with the error message.

    Notes:
        - Limits the number of articles to 10
        - Uses the GNews library to fetch news
        - Each article is formatted with its published date, title, and description
    """
    res = ''
    articlesLimit = 10
    
    try:
        google_news = GNews()

        keyword_news = google_news.get_news(keyword)
        
        for i in range(len(keyword_news)):
            if i >= articlesLimit:
                break
            res += "Published on: "+keyword_news[i]['published date'] + " -- " +"Title: "+keyword_news[i]['title'] +": "+ keyword_news[i]['description']+"\n"
            
    except Exception as e:
        res += f"Error from Google news: {e}"
        
    return res

import PyPDF2
import magic

def is_pdf_url(url: str) -> bool:
    """
    Detect if a URL points to a PDF file.
    
    Args:
        url (str): The URL to check
    
    Returns:
        bool: True if the content is a PDF, False otherwise
    """
    try:
        # Send a HEAD request first to minimize bandwidth
        response = requests.head(url, allow_redirects=True, timeout=10)
        
        # Check headers first
        if 'application/pdf' in response.headers.get('Content-Type', '').lower():
            return True
        
        # If headers don't confirm, do a full content check
        full_response = requests.get(url, stream=True, timeout=10)
        
        # Check MIME type using python-magic
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(full_response.content[:1024])
        
        return content_type == 'application/pdf'
    
    except Exception as e:
        print(f"PDF detection error for {url}: {e}")
        return False

def extract_pdf_text(url: str) -> str:
    """
    Extract text from a PDF URL.
    
    Args:
        url (str): URL of the PDF
    
    Returns:
        str: Extracted text from PDF
    """
    try:
        response = requests.get(url, timeout=30)
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text() + "\n\n"
        
        return full_text.strip()
    
    except Exception as e:
        print(f"PDF text extraction error for {url}: {e}")
        return ""


def get_text_from_url(url: str) -> str:
    """
    Crawl a webpage and extract text content using Selenium.

    Args:
        url (str): The web URL to crawl and extract content from.

    Returns:
        str: A formatted string containing:
            - Page titles
            - Page URLs
            - Page contents
            
    Notes:
        - Crawls a maximum of 2 pages
        - Uses a custom SeleniumCrawler with a max depth of 1
        - Disables robot.txt file checking
        - Closes the crawler after extraction
        - Handles PDF URLs with special parsing
    """    
    from webcrawler import SeleniumCrawler

    # Check if the URL is a PDF first
    if is_pdf_url(url):
        pdf_text = extract_pdf_text(url)
        return f"PDF URL: {url}\nContent:\n{pdf_text}"

    # Crawl on this number of pages
    max_url_count = 2
    max_depth = 2

    crawler = SeleniumCrawler(url, max_depth=max_depth, max_url_count=max_url_count-1, timeout_response=40)
    # Don't check robot.txt file on the server
    crawler.setCheckRobot(False)
    
    crawler.crawl(url)
    crawler.close()

    res = ''
    # Process results with PDF detection for each crawled URL
    for result in crawler.results:
        # Check if this result's URL is actually a PDF
        if is_pdf_url(result['url']):
            pdf_text = extract_pdf_text(result['url'])
            res += f"PDF Title: {result['title']}, URL: {result['url']}\n"
            res += f"PDF Content: {pdf_text}\n"
        else:
            # Regular webpage processing
            res += f"Title: {result['title']}, URL: {result['url']}\n"
            res += f"Content: {result['content']}\n"
        
        res += "-" * 80
        res += "\n"
        
    return res

def get_text_from_url2(url : str):
    """
    Extract text content from a webpage using requests and BeautifulSoup.

    Args:
        url (str): The web URL to extract text from.

    Returns:
        str: Extracted text content from the webpage, including:
            - Paragraphs
            - Table contents
            - Filtered text (without scripts, footers, etc.)

    Notes:
        - Uses BeautifulSoup for HTML parsing
        - Removes unwanted tags like footer, nav, script, style
        - Replaces links with their text content
        - Handles timeouts and request exceptions
        - Returns error messages if extraction fails
    """
    def convert_html_table_to_text(table):

        rows = []
        for row in table.find_all('tr'):
            # Get all cells (th and td) from the row
            cells = row.find_all(['th', 'td'])
            row_text = ' | '.join(cell.get_text().strip() for cell in cells)
            rows.append(row_text)
        
        return '\n'.join(rows)
    
    try:
        # Make the GET request to the proxy server
        response = requests.get(url, timeout=5) 
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Parse the HTML content
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted tags (equivalent to removeUnwantedTags)
        for tag_name in ['footer', 'nav', 'script', 'style']:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Replace links with their text content
        for link in soup.find_all('a'):
            link.replace_with(link.get_text())
        
        # Extract paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
        paragraphs = [p for p in paragraphs if p]  # Filter out empty paragraphs
        
        if not paragraphs:
            print("Warning: No paragraphs were found!")
        
        # Process tables
        for table in soup.find_all('table'):
            table_text = convert_html_table_to_text(table)
            paragraphs.append(table_text)
        
        # Join all text with double newlines
        text = '\n\n'.join(paragraphs)
        # print("\n\nWebsite returned : "+text+"\n\n",flush=True)
        return text
        
    except requests.exceptions.Timeout:
        print("The request timed out",flush=True)
        return f'Error fetching text from URL: Time Out!'
    except requests.exceptions.RequestException as error:
        print(f'Error fetching text from URL: {error}',flush=True)
        return f'Error fetching text from URL: {error}'



def safe_function_call(func: Callable, args: str) -> str:
    """
    Safely execute a function with provided arguments and handle potential exceptions.

    Args:
        func (Callable): The function to be called.
        args (str): JSON-formatted string of arguments for the function.

    Returns:
        str: Result of the function call or an error message.

    Notes:
        - Attempts to parse JSON arguments
        - Catches and handles various exceptions like JSON decoding, type errors
        - Converts function result to a string
        - Provides detailed error messages for debugging
    """
    try:
        
        print(args, flush=True)
        # Parse the JSON string into a Python dictionary
        
        # parsed_args = json.loads(args)
        # print(parsed_args,flush =True)
        
        # Call the function with the parsed arguments
        # result = func(**parsed_args)
        print(f"About to call {func.__name__} with arguments {args}",flush=True)
        result = func(args)
        
        # Ensure the result is a string
        return str(result)
    except json.JSONDecodeError as e:
        return f"Error parsing arguments for {func.__name__}: {str(e)}"
    except TypeError as e:
        # This can happen if the function doesn't accept the provided arguments
        return f"Invalid arguments for {func.__name__}: {str(e)}"
    except Exception as e:
        return f"Error calling {func.__name__}: {str(e)}"

# def process_tool_calls(response: Dict[str, Any], available_functions: Dict[str, Callable],image_list) -> str:
#     """
#     Process tool calls from a response and execute corresponding functions.

#     Args:
#         response (Dict[str, Any]): Response dictionary containing tool calls.
#         available_functions (Dict[str, Callable]): Dictionary of callable functions.
#         image_list (list): List of images to be used in function calls.

#     Returns:
#         str: Aggregated results of tool function calls.

#     Notes:
#         - Handles multiple tool calls in a single response
#         - Matches function names from response to available functions
#         - Supports image processing for functions requiring images
#         - Returns error messages for unmatched or failed function calls
#     """
    
#     if 'message' not in response or 'tool_calls' not in response['message']:
#         return 'No tool calls found in the response.'

#     results = []
#     for tool_call in response['message']['tool_calls']:
#         function_name = tool_call['function']['name']
#         function_args = tool_call['function']['arguments']
        
#         if "image" in function_args and image_list:
#             function_args["image"] = image_list[0]

#         if function_name not in available_functions:
#             results.append(f"Function '{function_name}' not found in available functions.")
#             continue

#         function_to_call = available_functions[function_name]
#         result = safe_function_call(function_to_call, function_args)
#         results.append(result)

#     return '. '.join(results)


from multiprocessing import Manager, Process
from typing import Dict, Any, Callable, List

def run_with_timeout(target_func, timeout, *args, **kwargs):
    """
    Runs a target function with a timeout.
    """
    process = Process(target=target_func, args=args, kwargs=kwargs)
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        print(f"Function {target_func.__name__} exceeded timeout and will be terminated.")
        process.terminate()
        process.join()

def process_tool_calls(response: Dict[str, Any], available_functions: Dict[str, Callable], image_list: List[Any], timeout: int = 300) -> str:
    """
    Process tool calls from a response and execute corresponding functions in parallel with timeouts.

    Args:
        response (Dict[str, Any]): Response dictionary containing tool calls.
        available_functions (Dict[str, Callable]): Dictionary of callable functions.
        image_list (list): List of images to be used in function calls.
        timeout (int): Maximum time (in seconds) allowed for each tool call.

    Returns:
        str: Aggregated results of tool function calls.
    """
    if 'message' not in response or 'tool_calls' not in response['message']:
        return 'No tool calls found in the response.'

    manager = Manager()
    results = manager.list()  # Shared list for collecting results

    def safe_function_wrapper(func, args_dict, results_buffer):
        try:
            # Directly call the function with the dictionary as the argument
            result = func(args_dict)
            results_buffer.append(result)
        except Exception as e:
            results_buffer.append(f"Error in function '{func.__name__}': {str(e)}")

    processes = []
    for tool_call in response['message']['tool_calls']:
        function_name = tool_call['function']['name']
        function_args = tool_call['function']['arguments']

        # Add an image if applicable
        if "image" in function_args and image_list:
            function_args["image"] = image_list[0]

        if function_name not in available_functions:
            results.append(f"Function '{function_name}' not found in available functions.")
            continue

        function_to_call = available_functions[function_name]
        process = Process(
            target=run_with_timeout,
            args=(safe_function_wrapper, timeout, function_to_call, function_args, results),
        )
        processes.append(process)
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()

    return '. '.join(results)





from urllib.parse import urlencode

def get_image_processing_results(objs):
    """
    Process and analyze an image using a specified image processing model.

    Args:
        objs (dict): Dictionary containing:
            - 'prompt' (str): Instructions or query for image analysis
            - 'image' (image blob): The image to be processed

    Returns:
        str: Detailed image analysis report including:
            - Text detection
            - Object recognition
            - Color analysis
            - Trend and data insights
            - Timestamp of analysis

    Notes:
        - Uses Ollama's LLaVA model for image processing
        - Prepends predefined instructions to user's prompt
        - Handles image recognition and text extraction
        - Returns error message if processing fails
    """

    print("\n>>>ENTRY: get_image_processing_results() \n\n",flush=True)
    image_processing_model = "llava:latest"
    # image_processing_model = "bakllava:latest"
    imgPrompt = ''
    img = None
    
    imgPrompt = str(objs.get('prompt', ''))
    img       = objs.get('image', None)
    
    if img == None or img == "None":
        return ""
    
    prePrompt = "INSTRUCTIONS: analyze the image very carefully and detect text and try to read them accurately. Detect objects, faces, and colors. If the image is a plot or a chart, observer the labels and values on the x and y axises. observer the trend and fluctuations in the graph as well as the legend and keys.  Only respond to what the user prompt asks for from the image and nothing else and keep your response precise and very short. USER PROMPT:  "
    imgPrompt = prePrompt + imgPrompt
    
    # print(f"Prompt Parameter : {imgPrompt}",flush=True)
    # print(f"Image Blob : {img}",flush=True)
    # print("\n\n",flush=True)
    
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    messages = [ 
            {
            "role" : "user", 
            "content" : imgPrompt,
            "images"  : img
            }
        ]
    # print("\n\n"+json.dumps(messages),flush=True)

    try:
        # print(f"\n\nCalling Model ==>{data["tools_calling_model"]}",flush=True)
        # print(f"---------- Prompt: {json.dumps(messages)}\n\n")
        response = ollama.chat(
            # model=data["model"],
            model=image_processing_model,
            messages=messages,
            stream=False
            
        )
        
        # print("\n\n"+json.dumps(response["message"]),flush=True)
        # print("\n\nResponse ->>: "+response["message"]["content"],flush=True)
        res = response["message"]["content"]
        
        res = f"\n\nHere is the image recognition and analysis report you requested as of [Current Date and Time: {todayStr}], use it to compose your response to the user\'s prompt:  {res}" 
        
        print("\n\n>>>EXIT: get_image_processing_results() \n\n",flush=True)
        return res  
    
    except Exception as e:
        print(f"Exception {e}",flush=True)
        return f"Error : {e}"




#######################################################
# Dictionary to hold news filters and corresponding URLs
def lookup_website(objs):
    """
    Retrieve and extract text content from a specified website URL.

    Args:
        objs (dict): Dictionary containing:
            - 'url' (str): The website URL to look up and extract content from

    Returns:
        str: Extracted website content with:
            - Current date and time
            - Text extracted from the webpage
            - Error message if extraction fails

    Notes:
        - Uses get_text_from_url() to extract webpage content
        - Handles exceptions during web crawling
        - Provides timestamp for the lookup
    """
    
    print("\n>>>ENTRY: lookup_website() \n\n",flush=True)

    url = ''
    url = objs.get('url', '')
    print(f"url = {url}", flush=True)
    
    if url == '':
        return "Sorry, I couldn't find anything."
        
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    try:
        web_results = get_text_from_url(url)
    
    except Exception as e:
        web_results = f"Error: Exception returned '{e}'. "
        
        
    res = f"\n\nAs of [Current Date and Time: {todayStr}] here are lookup results: \n" + web_results
    
    print("\n>>>EXIT: lookup_website() \n\n",flush=True)

    return res

NEWS_URLS = {
    "world": [
        "https://apnews.com/world-news",
        "https://www.aljazeera.com/europe/",
        "https://www.aljazeera.com/asia/",
        "https://www.aljazeera.com/asia-pacific/",
        "https://www.npr.org/sections/world/"
    ],
    "national": [
        "https://apnews.com/us-news",
        "https://www.reuters.com/world/us/",
        "https://www.aljazeera.com/us-canada/",
        "https://www.nytimes.com/section/us",
        "https://www.npr.org/sections/national/"
    ],
    "law": [
        "https://www.npr.org/sections/law/",
        "https://www.reuters.com/legal/"
    ],
    "politics": [
        "https://www.npr.org/sections/politics/"
    ],
    "business": [
        "https://www.npr.org/sections/business/",
        "https://www.reuters.com/business/"
    ],
    "fact_check": [
        "https://allsides.com/",
        "https://www.mediabiasfactcheck.com/"
    ],
    "finance": [
        "https://www.bea.gov/news/glance",
        "https://www.reuters.com/markets/global-market-data/",
        "https://www.cnbc.com/economy/",
        "https://finance.yahoo.com/topic/stock-market-news/",
        "https://www.reuters.com/markets/us/",
        "https://us.econoday.com/",
        "https://finance.yahoo.com/topic/latest-news/"
    ],
    "middle_east": [
        "https://apnews.com/hub/middlw-east",
        "https://www.reuters.com/world/middle-east/",
        "https://www.nytimes.com/section/world/middleeast",
        "https://www.aljazeera.com/middle-east/",
        "https://www.aljazeera.com/tag/israel-palestine-conflict/",
        "https://www.npr.org/sections/middle-east/"
    ],
    "science": [
        "https://www.reuters.com/technology/",
        "https://www.sciencenews.org/all-stories",
        "https://www.npr.org/sections/science/" ,
        "https://www.nasa.gov/news/all-news/"
    ],
    "news": [        
        "https://apnews.com/hub/ap-top-news",
        "https://www.apnews.com/",
        "https://www.reuters.com/",
        "https://www.aljazeera.com/news/",
        "https://www.npr.org/sections/news/",
        "https://www.aljazeera.com/middle-east/",
        "https://www.aljazeera.com/us-canada/",
        "https://www.nytimes.com/section/us"
    ],
    "default": [
        "https://apnews.com/hub/ap-top-news",
        "https://www.reuters.com/"
    ]
}


# Dictionary mapping synonyms to primary categories
SYNONYMS = {
    "fact_check": {"fact check","fact checking", "unbiased news"},
    "world": {"world", "global", "international"},
    "national": {"national", "nation", "domestic", "us", "usa", "american"},
    "law": {"law", "legal", "court", "courts", "justice", "judicial"},
    "politics": {"politics", "politicians", "political", "elections", "election", "nomination", "congress", "house of representatives", "senate", "senators"},
    "business": {"business", "trade", "commerce", "commercial", "retail", "running a business", "trading", "online business"},
    "financial": {"financial", "trade", "commerce", "commercial", "retail", "running a business", "macroeconomics", "microeconomics", "business cycle", "trading", "online business"},
    "finance": {"finance", "financial","stocks" ,"market" ,"markets", "stock" ,"stock market" ,"bond market", "securities", "inflation", "financing", "stock trading", "bonds", "interest rates", "fed rates", "fmoc", "us economy", "economy","economic","federal reserve"},
    "middle_east": {"middle east", "arab world", "near east", "palestine", "gaza","gulf" ,"israel", "egypt", "iran", "arabian", "iraq", "lebanon", "syria", "saudi arabia"},
    "science": {"science","scientific","physics","chemistry","biology","geology", "life science", "earth science","technology","bioscience","science research", "NASA", "space"}
}

def find_category(newsFilter):
    """
    Find the news category based on a given keyword or synonym.

    Args:
        newsFilter (str): Keyword to match against predefined news category synonyms.

    Returns:
        str: The matched news category or 'default' if no match is found.

    Notes:
        - Checks input against predefined SYNONYMS dictionary
        - Uses case-insensitive matching
        - Returns 'default' category if no match is found
    """
    # Convert to lowercase and split into words
    # filter_words = newsFilter.lower().split()
    # Split on separators except spaces within words or phrases
    filter_words = re.split(r'[,\.;:!?\-]+', newsFilter.lower())
    
    for category, synonyms in SYNONYMS.items():
        # Check if any word in the filter matches any synonym
        if any(word in synonyms for word in filter_words):
            return category
        
    return "default"

def get_news_summaries(objs):
    """
    Retrieve news summaries from multiple sources based on a given filter.

    Args:
        objs (dict): Dictionary containing:
            - 'filter' (str): Keyword to filter news sources and content

    Returns:
        str: Comprehensive news summary including:
            - Timestamp of retrieval
            - Google News results
            - Content from multiple news URLs
            - Error messages for failed URL retrievals

    Notes:
        - Uses find_category() to determine news category
        - Retrieves news from Google and predefined news URLs
        - Handles exceptions for each news source
        - Provides fallback to default URLs
    """
    
    print("\n>>>ENTRY: get_news_summaries() \n\n",flush=True)

    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")

    # Get the filter keyword from the user input and clean it up
    newsFilter = objs.get('filter', '').lower().strip()

    # Print the filter for debugging
    print(f"\n******************************\nget_news_summaries() Filter: {newsFilter}\n***************************\n\n", flush=True)

    # Find the corresponding category using the synonyms dictionary
    category = find_category(newsFilter)
    
    # Get the list of URLs based on the category
    urls = NEWS_URLS.get(category, NEWS_URLS["default"])
    
    # Initialize result string
    # Append current date and time
    res = f'\nFROM EXTERNAL SOURCES as of [Current Date and Time: {todayStr}]. Here is the News Summary you requested, use the summary to compose your response to the user\'s prompt:\n\n'
    
    res += get_news_from_google(newsFilter)

    # Fetch content from each URL and handle exceptions
    for newsURL in urls:
        try:
            res += "\n\nFrom Source: " + str(newsURL) + "\n" + get_text_from_url(url=str(newsURL)) + "\n\n"
        except Exception as e:
            res += f"Error fetching {newsURL}: {e}\n"

    print("\n>>>EXIT: get_news_summaries() \n\n",flush=True)   
    return res


import requests
import json
import wikipedia as wiki
from datetime import datetime
import re

def wikipedia_query(objs, language_code='en', number_of_results=10):
    """
    Search and retrieve Wikipedia information for a given query.

    Args:
        objs (dict): Dictionary containing:
            - 'question' (str): The search query
        language_code (str, optional): Language code for Wikipedia search. Defaults to 'en'.
        number_of_results (int, optional): Maximum number of search results. Defaults to 10.

    Returns:
        str: Wikipedia content including:
            - Page content or summary
            - Timestamp of retrieval
            - Latest relevant news
            - Error messages if search fails

    Notes:
        - Uses Wikimedia API for searching
        - Cleans and prepares search query
        - Handles disambiguation pages
        - Falls back to alternative results if primary search fails
        - Includes Google News related to the topic
    """
    
    # Get current date/time
    print("\n>>>ENTRY: wikipedia_query() \n\n",flush=True)

    question = ''
            
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    for key, value in objs.items():
        print(f"{key} = {value}",flush=True)
        if key == 'question':
            question = value
    
    # print(question,flush=True)
    print("Argument (question) = "+question,flush=True)

    if question == '':
        return '';
    
    if isinstance(question, str):
        question=str(question.strip().lower())
    
    # Clean and prepare the search query
    def prepare_query(query):
        # Remove question words and common filler words
        question_words = r'\b(what|who|where|when|why|how|is|are|was|were|do|does|did|can|could|would|should)\b'
        query = re.sub(question_words, '', query, flags=re.IGNORECASE)
        
        # Remove punctuation except for significant characters
        query = re.sub(r'[^\w\s-]', '', query)
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        return query
    
    # Prepare the API call
    base_url = 'https://api.wikimedia.org/core/v1/wikipedia/'
    endpoint = '/search/page'
    url = base_url + language_code + endpoint
    
    # Clean up the search query
    cleaned_query = prepare_query(question)

    # Try to get info from Britannica 
    
    # britannica_res = get_text_from_url(f"https://www.britannica.com/search?query={cleaned_query}")
    britannica_res = ''
    # print(f"\n\nBritannica Output: {britannica_res}")
    # Enhanced search parameters
    parameters = {
        'q': cleaned_query,
        'limit': number_of_results,
        'namespace': '*',  # Search all namespaces
        'sort': 'relevance',
        'offset': 0,
        'profile': 'engine_autoselect'
    }
    # print(json.dumps(parameters),flush=True)
    headers = {
        'User-Agent': 'python-requests/x',
        'Accept': 'application/json'
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the response
        res = response.json()
        
        if not res.get('pages'):
            print(f"Returning NOTHING!!", flush=True)
            return "Sorry, I couldn't find any relevant results."
        
        # Try multiple results if the first one fails
        for page_result in res['pages'][:3]:  # Try up to 3 results
            try:
                queryPage = str(page_result['title'])
                print(f"Trying page with Title: {queryPage}", flush=True)
                
                # Configure Wikipedia search settings
                # wiki.set_rate_limiting(True)
                wiki.set_lang(language_code)
                
                # Try to get the page
                page = wiki.page(queryPage, auto_suggest=True,redirect=True, preload=True)
                
                # Get google news for this title
                googleNews = get_news_from_google(queryPage)
                
                # if relevance_score > 0:  # If there's some relevance
                print(f"##################### Returned Text From Primary",flush=True)
                # return f"\n\nFROM EXTERNAL SOURCE (Wikipedia) as of [Current Date and Time: {todayStr}]. Use the following text to compose your response to user's prompt:\"\"\" {page.summary.replace('\"', '\'')} \"\"\" Prompt: {question}"
                return f"\n\nFROM EXTERNAL SOURCE (Wikipedia) as of [Current Date and Time: {todayStr}]. Use the following text to compose your response to user's prompt:\"\"\"\n\nSource 1: {json.dumps(page.content)}.\n\n Latest relevant news: {googleNews} \"\"\" Prompt: {question}"
                # else:
                #     print(f"Pages do NOT exist!!!!",flush=True)
                    
            except wiki.exceptions.DisambiguationError as e:
                print(f"Exception 1-A: {e}",flush=True)
                # If disambiguation page, try the first suggested page
                try:
                    page = wiki.page(e.options[0], auto_suggest=False)
                    
                    # if page.exists():
                    print(f"##################### Returned Text From Exception",flush=True)
                    # return f"\n\nFROM EXTERNAL SOURCE (Wikipedia) as of [Current Date and Time: {todayStr}]. Use the following text to compose your response to user's prompt:\"\"\" {page.summary.replace('\"', '\'')} \"\"\" Prompt: {question}"
                    return f"\n\nFROM EXTERNAL SOURCE (Wikipedia) as of [Current Date and Time: {todayStr}]. Use the following text to compose your response to user's prompt:\"\"\"\n\nSource 1: {json.dumps(page.content)}.\n\n Latest relevant news: {googleNews}  \"\"\" Prompt: {question}"
                except:
                    print(f"Exception 1-B {e}",flush=True)
                    continue
                    
            except Exception as e:
                print(f"Exception 2-A {e}",flush=True)
                continue
        
        return "Sorry, I couldn't find a relevant Wikipedia article for your query."
        
    except requests.exceptions.RequestException as e:
        print(f"Error 1: {e}",flush=True)
        return f"Error making the API request: {str(e)}"
    except Exception as e:
        print(f"Error 2: {e}",flush=True)
        return f"An unexpected error occurred: {str(e)}"


# The following function is to be deprecated 
def wikipedia_query_old(objs):

    
    print("\n>>>ENTRY: wikipedia_query() \n\n",flush=True)

    question = ''
            
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    for key, value in objs.items():
        print(f"{key} = {value}",flush=True)
        if key == 'question':
            question = value
    
    # print(question,flush=True)
    # print("Argument (question) = "+question,flush=True)

    if question == '':
        return '';
    
    if isinstance(question, str):
        question=str(question.strip())
    
    # Create Wikipedia API object
    try :
        wiki = wikipediaapi.Wikipedia(user_agent='python-requests/x',language='en')
    
    except Exception as e:
        return f"Sorry, I couldn't find anything on that topic. Error: {e}"
    
    # Define regular expression pattern to match a question
    pattern = r"^(?:what|who|when|where|why|how)(?:\s+(?:is|are|was|were|will|can|could|should|would))?\s+(.+?)(?:[\s\?])?$"

    # # Take user input as question
    # question = str(text)

    # Apply pattern to the question
    match = re.match(pattern, question.lower())

    if match:
        # Replace the matched text with the corresponding query string
        query = match.group(1)
        query = query.strip()
    else:
        # If no pattern matches, use the original question as the query
        query = question.strip()

    # search for the right page
    language_code = 'en'
    search_query = query
    number_of_results = 1
    headers = {
    # 'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'User-Agent': 'python-requests/x'
    }

    base_url = 'https://api.wikimedia.org/core/v1/wikipedia/'
    endpoint = '/search/page'
    url = base_url + language_code + endpoint
    parameters = {'q': search_query, 'limit': number_of_results}
    response = requests.get(url, headers=headers, params=parameters)
    
    # Get the full result
    res = json.loads(response.text)
    
    # extract the page title
    queryPage = str(res['pages'][0]['title'])

    # Search Wikipedia for the page
    # print(f"q = {queryPage}", flush=True)
    
    try:
        page = wiki.page(queryPage)
        pageText = page.text
        
    except Exception as e:
        return f"Sorry, I couldn't find anything on that topic. Error: {e}"
    
    # Print the summary of the Wikipedia page
    
    print("\n>>>EXIT: wikipedia_query() \n\n",flush=True)
    if page.exists():
        return f"\n\nFROM EXTERNAL SOURCE (Wikipedia) as of [Current Date and Time: {todayStr}]. Use the following text to compose your response to user's prompt:\"\"\" "+page.summary.replace("\"","'")+" \"\"\" " + "Prompt: "+query
    else:
        return ''
    


def get_the_secret_tool(secret_tool):
    """
    Retrieve a predefined "secret" tool message.

    Args:
        secret_tool (str): A placeholder argument for the secret tool.

    Returns:
        str: A message containing:
            - Current timestamp
            - Hardcoded secret tool message

    Notes:
        - Primarily a placeholder or demonstration function
        - Always returns the same predefined message
        - Includes current date and time
    """
    
    print("\n>>>ENTRY: get_the_secret_tool() \n\n",flush=True)

    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")

    print("\n>>>EXIT: get_the_secret_tool() \n\n",flush=True)
    return f"\n[Current Date and Time: {todayStr}] \n\nFrom Tool: The secret tool is 'Open Sesame!.' \n"

def get_stock_and_company_data(objs):
    """
    Retrieve comprehensive stock and company financial information.

    Args:
        objs (dict): Dictionary containing:
            - 'symbol' (str): Stock ticker symbol or 'market' for S&P 500

    Returns:
        str: Detailed stock and financial information including:
            - Company financials
            - Stock information
            - Growth estimates
            - News headlines
            - Economic news
            - Current timestamp

    Notes:
        - Uses Yahoo Finance (yf) to fetch stock data
        - Converts financial data to CSV
        - Retrieves company information, news, and growth estimates
        - Fetches current economic news
        - Handles potential exceptions during data retrieval
    """
    
    print("\n>>>ENTRY: get_stock_and_company_data() \n\n",flush=True)

    symbol = ''
    symbol = objs.get('symbol', '')
    print(f"symbol = {symbol}", flush=True)
    
    if symbol == '' or symbol == 'None' or symbol == None:
        return "Sorry, I couldn't find anything."
    
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    if symbol.lower() == "market":
        symbol = "^GSPC"
    
    res = ''
    
    str_result = ""

    try:
        print(f"Getting Ticker financials for {symbol}",flush=True)
        tkr = yf.Ticker(symbol)
        df_fin = tkr.financials
        
    except Exception as e:
        return f"Sorry, I couldn't find anything on that topic. Error: {e}"
        
    try:
        print(f"Getting Ticker info for {symbol}",flush=True)
        json_list = [tkr.info]
        json_result = [item for item in json_list]  # Converting JSON string to Python dictionary/list
    
        df_fin_html = df_fin.to_csv(index=True, header=True)
    
        for i, item in enumerate(json_list):
            for key, value in item.items():
                # Convert both keys and values to strings before adding to result
                str_result += f"\n ({i+1}) '{str(key)}' : '{str(value)}',\n\n"
                i=i+1
                
    except Exception as e:
        str_result += f"Error Parsing Ticker results : {e}\n"
        
    # Get current economic status
    econNews ='\n\n#Here is the current state of the US Economy:\n\n'
    newsURL = "https://www.bea.gov/news/glance"
    try:
        econNews += get_text_from_url(url=str(newsURL)) 
        econNews += "\n\n"
    except Exception as e:
        econNews += f"get_text_from_url() Error: {e}\n"
    
    res = f'\n\nHere is the latest company data for stock symbol "{symbol}":' + df_fin_html
    
    markdown = "\n# News Headlines and Articles\n\n"
    
    news_objects = tkr.news
    for news in news_objects:
        title = news.get('title', 'No title')
        link = news.get('link', '#')
        
        # Create markdown block for each article
        markdown += f"## {str(title)}\n"
        markdown += f"[Read more]({str(link)})\n\n"
        markdown += "---\n\n"
    
    googleNews = ''
    
    try:
        googleNews = "Latest news from Google News: "+ get_news_from_google("stock market "+symbol)
    except Exception as e:
        googleNews = f"get_news_from_google() Error: {e}"
        
    print(f"About to call Ticker growth_estimates : {symbol}")
    growth_est = ''
    try:
        growth_est += "\nHere are the latest Growth Estimates Table:\n" + str(tkr.growth_estimates) + "\n------------\n"
    except Exception as e:
        growth_est = ''
        
    res += f'\n\nHere is the latest stock information for the stock as of [Current Date and Time: {todayStr}]: ' + str_result + growth_est + markdown + googleNews + econNews

    # print(res, flush=True)
    print("\n>>>EXIT: get_stock_and_company_data() \n\n",flush=True)
    return res

from time import sleep

from duckduckgo_search import DDGS
def ducducgo(query, max_results=3):
    """
    Perform web search using DuckDuckGo and retrieve search results.

    Args:
        query (str): Search term or query.
        max_results (int): Maximum number of search results to retrieve.

    Returns:
        str: Formatted search results including:
            - Result details (title, description, link)
            - Extracted content from linked pages
    """
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
            res = ''
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No Title')
                href = result.get('href', 'No URL')
                body = result.get('body', 'No Description')
                res += f"\nResult {i}:\nTitle: {title}\nURL: {href}\nDescription: {body}\n"
                # If you have a function to extract content from the URL, you can call it here
                if href != 'No URL':
                    content = get_text_from_url(href)
                    res += f"Content: {content}\n"
            return res
    except Exception as e:
        print(f"DuckDuckGo Error: {e}", flush=True)
        return f"An error occurred during the web search query '{query}'."
    
def search_web(objs):
    """
    Perform a web search and retrieve results.

    Args:
        objs (dict): Dictionary containing:
            - 'query' (str): Search term or query

    Returns:
        str: Web search results including:
            - Current timestamp
            - Search results from DuckDuckGo
            - Error message if search fails

    Notes:
        - Uses ducducgo() for web searching
        - Limits search to 3 results by default
        - Provides timestamp with search results
        - Handles exceptions during web search
    """
    print("\n>>>ENTRY: search_web() \n\n", flush=True)

    query = objs.get('query', '').strip()
    print(f"query = {query}", flush=True)
    
    if not query:
        return "Sorry, I couldn't find anything."
        
    today = datetime.now()
    todayStr = today.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
    
    max_results = 3
    
    try:
        # Assume ducducgo returns a list of search results
        web_results = ducducgo(query, max_results)
        if isinstance(web_results, list):
            web_results = '\n'.join(web_results)  # Convert list to a newline-separated string
    except Exception as e:
        web_results = f"Error: Exception returned in search_web(): '{e}'."
        
    res = (
        f"\n\nAs of [Current Date and Time: {todayStr}] "
        f"here are the web search results:\n{web_results}"
    )
    
    print("\n>>>EXIT: search_web() \n\n", flush=True)
    return res

    
    
available_functions = {
    'get_the_secret_tool': get_the_secret_tool,
    'wikipedia_query' : wikipedia_query,
    'get_stock_and_company_data' : get_stock_and_company_data,
    'get_news_summaries' : get_news_summaries,
    'get_image_processing_results' : get_image_processing_results,
    'search_web' : search_web,
    "lookup_website" : lookup_website
}

def extract_prompt(text):
    # Find the position of ' Prompt :' and return everything from that point onward
    prompt_start = text.find(' Prompt :')
    
    if prompt_start != -1:
        # Return the substring starting from ' Prompt :'
        return text[prompt_start:]
    else:
        # Return the original string if ' Prompt :' is not found
        return text

###################################################################################################################
############################################ ENDS of Tools Functions ##############################################

import os
os.environ["USER_AGENT"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"


import ollama
import time
from langchain_ollama import OllamaLLM  # New import
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from text_chunker import TextChunker

@app.route('/llama3_1b/stream', methods=['POST'])

def stream_proxy():
        
    tools_in_use = True
    search_web_in_use = False
    tools_results = ''
    tools_results_summary = ''
    full_tools_text = ''
    
    OLLAMA_URL = "http://127.0.0.1:11434/api/generate"  # Adjust this URL if needed
    with lock:
        if request.method == 'POST':
            # data = request.json
            data = request.get_json()
            user_prompt = data['prompt']
            print(f"\n\nUser prompt : {data['prompt']}\n\n",flush=True)
            
            context = data['prompt_context']
            
            #################################################################################
            ##                  CONTEXT MANAGEMENT WITH and WITHOUT TOOLS                  ##            
            #################################################################################

            # print(f"\n\n========================================\ncontext\n=====================\n{context}\n=======================================\n\n")
            if "toolsInUse" in data:
                tools_in_use = data["toolsInUse"]
            print(f"\n\n##### toolsInUse from the client = {tools_in_use}\n\n",flush=True)
            
            if "searchWebInUse" in data:
                search_web_in_use = data["searchWebInUse"]
            # print(f"\n\n##### searchWebInUse from the client = {search_web_in_use}\n\n",flush=True)
            # print("Data in : ->",json.dumps(data,indent=4),flush=True)


            image_exists = False
            if "images" in data:
                if data["images"][0] != "noimage":
                    print("Request has Image ......",flush=True)
                    image_exists = True
            

            # ###########################################################################
            # Add if tool use is selected
            if (tools_in_use):   
                print("---> Tools are in use",flush=True)
                # user_prompt_only = extract_prompt(in_prompt)
                messages = [                         
                        {
                            "role": "system",
                            "content": """BEFORE YOU MAKE FUNCTION CALLS, FOLLOW THIS GUIDELINE:
                            Tool Call Generation Guidelines -->:
                        DO NOT USE MORE THAN THREE (3) DIFFERENT FUNCTIONS. YOU CAN CALL THE SAME FUNCTION MULTIPLE TIMES WIth DIFFERENT PARAMETERS  :
                        
                        Execution Strategy:
                        - Analyze the entire input comprehensively
                        - Select only the tools needed and most relevant to the prompt in most logical sequence
                        - Prioritize precision and relevance
                        - Avoid redundant or unnecessary tool calls.
                        - Ensure each function is called with relevant and required parameters
                        - Use exact proper nouns or specific topics as parameters
                        
                        1. Initial Context Retrieval:
                        - Always begin by calling get_the_secret_tool() to obtain the current date and time
                        - This ensures all subsequent tool calls have accurate temporal context
                        - Depending on the information needed, select a maximum of 2 tools out of the list and call them with more than once if needed with relevant parameters

                        2. Stock and Financial Information:
                        - For stock data, call get_stock_and_company_data() 
                            * One distinct call per stock symbol
                            * Use exact stock ticker as parameter
                        - For additional market context, use get_news_summaries() 
                            * Apply relevant keyword as parameter
                            * Focus on financial keywords related to the stock/sector

                        3. Current Events, Up-to-date Data, and Local Information
                        - Use search_web() for:
                            * Local events
                            * Current business information
                            * Addresses
                            * Contact details
                            * Real-time local context
                        - For deeper and current news context, supplement with get_news_summaries()

                        4. News and Current Affairs:
                        - Use get_news_summaries() for:
                            * Latest developments in major topics
                            * Global/national events
                            * Specific sectors (economy, politics, military)
                        - When local news is needed, include location specifics 
                            (city, state, country) in the parameter

                        5. Travel and Lifestyle Information:
                        - Employ search_web() for comprehensive queries about:
                            * Flight details
                            * Hotel availability
                            * Vacation destinations
                            * Rental information
                            * Tourist attractions
                        - Use full, detailed query strings
                        
                        6. Encyclopedia and Factual Information: 
                        - Divide the question into partial questions. Use wikipedia_query() only if needed. Call wikipedia_query() once per question as parameter for the following cases:
                            * Historical events
                            * Academic facts
                            * Biographical information
                            * Geographical details
                            * Definitional content
                            * Example Prompt: "Compare the Roman Empire with the Persian Empire and describe their strength and weaknesses." 
                                --> Respond with : tool_calls : wikipedia_query() with {'question'='roman empire'} then call wikipedia_query() again with {'question' : 'persian empire'} 
                            
                            
                        7. Ambiguous or Undefined Requests:
                        - If the input lacks clear actionable context or the need for external data, then
                            * Do NOT generate unnecessary function calls
                            * Return an empty list of function calls
                            * Ask user for clarification
                        
                        8. CRITICAL: Do NOT use wikipedia_query() for:
                            * Current news
                            * Recent events
                            * Breaking stories
                        
                        """
                        },
                        {
                            "role": "user",
                            "content" : """Examine the intent of the user's prompt and apply the system directives to make the appropriate calls to the tools' functions. 
                                            User Prompt: """ + context + user_prompt,
                            "images"  : data["images"] if image_exists else None
                        }
                    ]
                
                # print("messages :",messages,flush=True)
                
                # print(f"--> context: {context}",flush=True)
                # print(f"Tools Calling Model : {data["tools_calling_model"]}",flush=True)            
                try:
                    print(f"\n\nCalling Tools Model ==>{data["tools_calling_model"]}",flush=True)
                    # print(f"---------- Prompt: {json.dumps(messages)}\n\n")
                    response = ollama.chat(
                        # model=data["model"],
                        model=data["tools_calling_model"].strip(),
                        messages=messages,
                        options={
                            'temperature':0,
                            },
                        tools=data["tools"],
                        think=False
                    )
                    
                    print("********************************\nollama.chat() response : --> \n\n"+ json.dumps(response['message']['content']),flush=True)

                except Exception as e:
                    @stream_with_context
                    def error_gen(e):
                        print(f"Exception {e}",flush=True)
                        # Yielding error in event stream format
                        yield "data: {\"error\": \"" + str(e) + "\",\"done\" : true }\n\n"
                        # Indicating that the stream is done
                        # yield "data: {\"done\": true}\n\n"
                    if "does not support tools" in str(e):
                        error_str = f"Error: {data["tools_calling_model"]} Does not support tools calling. Use a different model in the seetingings panel."
                        print(f"\n\n*Calling Model (EXCEPTION) ==>{data["tools_calling_model"]}",flush=True)
                        # print(f"---------- Prompt: {json.dumps(messages)}\n\n")

                        print(f"\n\nCalling BACKUP Tools Model ==> llama3.2:3b",flush=True)
                        response = ollama.chat(
                                model="llama3.2:3b",
                                messages=messages,
                                options={
                                    'temperature':0,
                                    },
                                tools=data["tools"]
                        )
                    else:
                        # Pass the exception 'e' to the generator function
                        return Response(error_gen(e), content_type='text/event-stream')

                if 'tool_calls' in response['message']:
                    print("\nAttempting a TOOL CALL:",flush=True)
                    
                    print("********************************\nollama.chat() response : --> \n\n"+ json.dumps(response['message']['content']),flush=True)
                    # Process tool calls
                    image_list = [data["images"]] if image_exists else None
                    
                    tools_results = process_tool_calls(response, available_functions,image_list)

            ########################## End tool Use ###########################################

            context_size = len(context)
            tool_results_size = len(tools_results)
            system_prompt_size = len(data['system'])
            max_context_window = 65536 # 64k bytes 
            max_context_tokens = max_context_window / 4 # estimating 4 bytes per token
            full_tools_text = context +  ".\n" + tools_results


            # If total context size with tool results or without (full_tools_text) exceeds max_context_window (adjusted) thne try to shorten it
            if (len(full_tools_text) > (max_context_window) * 1.05):
                try:
                    print(f"\n Calling TextChumker() to reduce context size from {len(full_tools_text)} to around {max_context_window} bytes \n\n", flush=True)
                    tools_results_summary = TextChunker.summary_by_semantics(full_tools_text, query=data['system']+' \n'+ user_prompt,max_length=max_context_window)
                    # tools_results_summary = TextChunker.filter_text(input_text=tools_results,prompt=user_prompt,max_output_length=8192)
                    print(f" --->> TextChunker() was called and returned tools_results_summary size of {len(tools_results_summary)} bytes. From {len(full_tools_text)}\n\n", flush=True)
                except Exception as e:
                    print(f"Error: exception in TextChunker.summary_by_semantics() call. Function returned message: {e}", flush=True)
                    tools_results_summary = full_tools_text # TextChunker() failed!! Use the full text
            else:
                tools_results_summary = full_tools_text


            if tools_in_use:    
                print(f"""\n\n###################################################\nTOOLS RESULTS SUMMARY: \n###################################################\n\n{tools_results_summary}\n====================\n\n
                      Context Size (before tool call)= {context_size} bytes
                      Tool_Results_Size = {tool_results_size} bytes
                      System Prompt Size = {system_prompt_size} bytes
                      Full Text Size (context + tools_results) = {len(full_tools_text)} bytes
                      ==> Tool Results Summary Size = {len(tools_results_summary)} bytes
                      \n\n====================\nEND OF TOOLS RESULTS SUMMARY\n=================\n\n""",flush=True)
            else:
                print(f"""\n\n###################################################\nFULL CONTEXT (NO TOOLS): \n###################################################\n\n{tools_results_summary}\n====================\n\n
                    Context Size (no tools call)= {context_size} bytes
                    System Prompt Size = {system_prompt_size} bytes
                    Full Text Size (no tools call) = {len(full_tools_text)} bytes
                    \n\n====================\nEND OF CONTEXT \n=================\n\n""",flush=True)
                         
            in_prompt = "Context: "+tools_results_summary +" \n"+ user_prompt
            
            print(f"\n\nin_prompt size = {in_prompt} bytes\n")
            
            #################################################################################
            ##              END CONTEXT MANAGEMENT WITH and WITHOUT TOOLS                  ##            
            #################################################################################
            # ###############################################################################

            payload = {
                "model": data['model'],
                # "prompt": data['prompt'],
                "prompt": in_prompt,
                "system": data['system'],
                "options":{
                    "temperature" : data['temperature'],
                    "top_k" : data['top_k'],
                    "top_p" : data['top_p'],
                    "num_ctx" : data['num_ctx'],
                    "low_vram" : data.get('low_vram', False)
                },
                "think": False,  # Set to False to disable thinking
                "stream": data.get('stream', True)
            }
            
            # payload["images"] = [data["images"]] if image_exists else None
            payload["images"] = data["images"] if image_exists else None
                
            print(f"\n\n*Primary Calling Model ==>{data["model"]}",flush=True)
            # print(f"---------- inPrompt: {in_prompt}\n\n")

            # print("Here is my payload:")
            # print("Payload : ->"+json.dumps(payload,indent=3),flush=True)
            
            # Initialize the new LLM class
            # llm = OllamaLLM(model=data['model'],
            #                 temperature=data['temperature'],
            #                 num_ctx=data['num_ctx'],
            #                 image_list=payload["images"],
            #                 top_k=data['top_k'],
            #                 top_p=data['top_p'],
            #                 num_gpu=1, format='json')

            @stream_with_context
            def generate():
                headers = {'Content-Type': 'application/json'}
                try:
                    # with requests.post(OLLAMA_URL, json=data, headers=headers, stream=True) as response:
                    # print("About to call "+'http://127.0.0.1:11434/api/generate'+"\n",flush=True)
                    with requests.post('http://127.0.0.1:11434/api/generate', json=payload, headers=headers, stream=True) as response:
                    # with requests.post('http://127.0.0.1:11434/api/chat', json=payload, headers=headers, stream=True) as response:
                        response.raise_for_status()
                        # print("Returned from "+'http://127.0.0.1:11434/api/generate'+"\n",flush=True)
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                # print("decoded_line : ", decoded_line,flush=True)
                                
                                json_object = json.loads(decoded_line)
                                
                                # print("json_object['response'] : ",json_object["response"],flush=True)
                                # yield f"data: {decoded_line}\n\n"
                                
                                # Experimental code
                                response_text = json_object.get("response", "")
                                # print("response_text : ",response_text, flush=True)

                                # Escape { and } in the response field
                                response_text = response_text.replace('{', '\\{').replace('}', '\\}')
                                
                                # Update the json_object with the escaped response text
                                json_object["response"] = response_text
                                
                                # Serialize the JSON object back to a JSON string
                                escaped_json_string = json.dumps(json_object)
                                
                                # Yield the escaped JSON string as part of the server-sent event
                                yield f"data: {escaped_json_string}\n\n"
                
                except requests.RequestException as e:
                    print(f"data: {json.dumps({'error': str(e)})}\n\n", flush=True)
                    def error_gen():
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    return Response(error_gen(), content_type='text/event-stream')
                yield "data: {\"done\": true}\n\n"
            
            return Response(generate(), content_type='text/event-stream')
        else:
            # Handle GET request for EventSource
            def generate():
                yield "data: {\"connected\": true}\n\n"
            return Response(generate(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Change to debug=False for production

