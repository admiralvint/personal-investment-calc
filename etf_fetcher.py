"""
ETF Data Fetcher using Yahoo Finance or Local CSV.

Prioritizes local CSV files ({ISIN}.csv) if available.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
import os
import numpy as np
import pandas as pd
import yfinance as yf


# ISIN to Yahoo Finance ticker mapping for common ETFs
ISIN_TO_TICKER = {
    'IE00BK5BQT80': 'VWCE.DE',
    'IE00B4L5Y983': 'IWDA.AS',
    'IE00B3RBWM25': 'VUSA.L',
    'IE00BKX55T58': 'VWRL.L',
    'LU0392494562': 'EXSA.DE',
    'IE00B5BMR087': 'CSPX.L',
    'IE00BJ0KDQ92': 'XDWL.DE',
    'IE00B3XXRP09': 'VUSA.AS',
}


@dataclass
class ETFData:
    """Container for ETF historical data and statistics."""
    isin: str
    ticker: str
    name: str
    annual_return: float
    annual_volatility: float
    years_of_data: int
    last_price: float
    currency: str
    
    def to_dict(self) -> dict:
        return {
            'isin': self.isin,
            'ticker': self.ticker,
            'name': self.name,
            'annual_return': round(self.annual_return * 100, 2),
            'annual_volatility': round(self.annual_volatility * 100, 2),
            'years_of_data': self.years_of_data,
            'years': self.years_of_data,
            'last_price': round(self.last_price, 2),
            'currency': self.currency
        }


def isin_to_ticker(isin: str) -> Optional[str]:
    isin = isin.upper().strip()
    return ISIN_TO_TICKER.get(isin)


def fetch_from_csv(isin: str, filepath: str) -> Optional[ETFData]:
    """Fetch data from a local CSV file."""
    try:
        # Read without header first
        df = pd.read_csv(filepath, header=None)
        
        # Heuristic to detect header
        # Check first row values
        first_row = df.iloc[0].astype(str).str.lower().tolist()
        has_header = any('date' in x for x in first_row) or any('close' in x or 'price' in x for x in first_row)
        
        if has_header:
            # Reload with header or just set columns from first row
            df.columns = df.iloc[0]
            df = df[1:]
            
        # Normalize columns
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Identify Date and Close columns
        date_col = next((c for c in df.columns if 'date' in c), None)
        close_col = next((c for c in df.columns if any(x in c for x in ['close', 'price', 'nav', 'value'])), None)
        
        # Fallback for headerless: assume 0=Date, 1=Close
        if not date_col or not close_col:
            if not has_header and len(df.columns) >= 2:
                # Assuming Col 0 is Date, Col 1 is Close
                df = df.rename(columns={df.columns[0]: 'Date', df.columns[1]: 'Close'})
                date_col = 'Date'
                close_col = 'Close'
            else:
                 print(f"CSV {filepath} must have 'Date' and 'Close' columns.")
                 return None
        else:
            df = df.rename(columns={date_col: 'Date', close_col: 'Close'})

        # Parse Dates
        # Filter garbage (like 0000-00-00)
        df = df[df['Date'].astype(str).str.match(r'\d{4}-\d{2}-\d{2}')]
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date').sort_index()
        
        # Ensure Close is numeric
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df.dropna(subset=['Close'])
        
        if df.empty or len(df) < 20:
            return None

        # Metrics
        daily_returns = df['Close'].pct_change().dropna()
        total_return = (1 + daily_returns).prod()
        trading_days = len(daily_returns)
        years_actual = trading_days / 252 # Approx
        
        if years_actual < 0.1: return None
        
        annual_return = total_return ** (1 / years_actual) - 1
        annual_volatility = daily_returns.std() * np.sqrt(252)
        last_price = df['Close'].iloc[-1]
        
        return ETFData(
            isin=isin,
            ticker=isin, # Use ISIN as ticker for local
            name=f"{isin} (Local CSV)",
            annual_return=annual_return,
            annual_volatility=annual_volatility,
            years_of_data=int(years_actual),
            last_price=last_price,
            currency="EUR" # Assume EUR for local CSV?
        )
    except Exception as e:
        print(f"Error reading CSV {filepath}: {e}")
        return None


@lru_cache(maxsize=20)
def fetch_etf_data(isin: str, years: int = 15) -> Optional[ETFData]:
    """
    Fetch ETF data from Local CSV or Yahoo Finance.
    """
    isin_upper = isin.upper().strip()
    
    # 1. Check Local CSV in current dir or /data
    cwd = os.getcwd()
    csv_candidates = [
        os.path.join(cwd, f"{isin_upper}.csv"),
        os.path.join(cwd, f"{isin_upper}.CSV"),
        os.path.join(cwd, "data", f"{isin_upper}.csv")
    ]
    
    for csv_path in csv_candidates:
        if os.path.exists(csv_path):
            print(f"Found local CSV for {isin_upper}: {csv_path}")
            data = fetch_from_csv(isin_upper, csv_path)
            if data: return data
    
    # 2. Fallback to Yahoo Finance
    print(f"No local CSV found for {isin_upper} (Checked: {csv_candidates[0]}). Trying Yahoo Finance...")
    
    ticker_symbol = isin_to_ticker(isin_upper)
    if not ticker_symbol:
        ticker_symbol = isin_upper
    
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=f"{years}y")
        if hist.empty:
             hist = ticker.history(period="max")
             
        if hist.empty or len(hist) < 20: 
            print(f"Yahoo Finance returned no data for {ticker_symbol}")
            # --- Fallback for Known Assets ---
            if isin_upper == 'TNESCFD' or 'TRIGON' in isin_upper:
                print("Using user-provided params for Trigon.")
                return ETFData(
                    isin=isin_upper,
                    ticker=isin_upper,
                    name="Trigon Dividend Fund (User Data)",
                    annual_return=0.125,     # ~12.5% (Based on 1y 12.4% & 3y 44.9%)
                    annual_volatility=0.15,  # 15% Est
                    years_of_data=3,
                    last_price=16.50,
                    currency="EUR"
                )
            return None
            
        daily_returns = hist['Close'].pct_change().dropna()
        total_return = (1 + daily_returns).prod()
        years_actual = len(daily_returns) / 252
        if years_actual < 0.1: return None
        
        annual_return = total_return ** (1 / years_actual) - 1
        annual_volatility = daily_returns.std() * np.sqrt(252)
        
        info = ticker.info
        name = info.get('longName', info.get('shortName', ticker_symbol))
        currency = info.get('currency', 'EUR')
        last_price = hist['Close'].iloc[-1]
        
        return ETFData(
            isin=isin_upper,
            ticker=ticker_symbol,
            name=name,
            annual_return=annual_return,
            annual_volatility=annual_volatility,
            years_of_data=int(years_actual),
            last_price=last_price,
            currency=currency
        )
        
    except Exception as e:
        print(f"Error fetching {isin}: {e}")
        return None
