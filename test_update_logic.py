from GoogleNews import GoogleNews
import pandas_datareader.data as web
import datetime
import pandas as pd

def test_news():
    print("--- Testing Google News ---")
    try:
        googlenews = GoogleNews(lang='en', period='1d')
        googlenews.search("Stock Market")
        result = googlenews.result()
        print(f"News Count: {len(result)}")
        if result:
            print(f"First News: {result[0]['title']}")
    except Exception as e:
        print(f"News Error: {e}")

def test_fred():
    print("\n--- Testing FRED Data ---")
    start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    end = datetime.datetime.now().strftime('%Y-%m-%d')
    try:
        d = web.DataReader("T10Y2Y", "fred", start, end)
        print(f"FRED Data (T10Y2Y):\n{d.tail()}")
    except Exception as e:
        print(f"FRED Error: {e}")

if __name__ == "__main__":
    test_news()
    test_fred()
