import yfinance as yf

try:
    print("Fetching data for AAPL...")
    aapl = yf.Ticker("AAPL")
    hist = aapl.history(period="1d")
    print("Data fetched successfully:")
    print(hist)
except Exception as e:
    print(f"An error occurred: {e}")
