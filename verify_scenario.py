
import numpy as np
import yfinance as yf
from monte_carlo import MonteCarloSimulator, PortfolioETF, Contribution, calculate_loan_evolution

def run_verification():
    # Parameters
    start_year = 2026
    end_year = 2036
    start_month = 4  # April
    
    initial_loan = 83000
    initial_capital = 83000
    
    # Contributions
    contribs = [
        Contribution("Adult1", 500),
        Contribution("Adult2", 300),
        Contribution("Laps1", 150),
        Contribution("Laps2", 150)
    ]
    total_monthly = sum(c.monthly_amount for c in contribs)
    
    # ETF Config (VWCE - IE00BK5BQT80)
    # Fetching real data or using app defaults. 
    # App default for VWCE often used: 8.5% return, 15% vol roughly.
    # Let's try to fetch actual recent metrics if possible, or use standard approximation.
    # For verification "consistency", I should use what the app likely uses.
    # The app fetches via yfinance. I will do same.
    
    print(f"Fetching data for IE00BK5BQT80 (VWCE.DE)...")
    ticker = "VWCE.DE"
    try:
        data = yf.download(ticker, period="5y", interval="1mo", progress=False)
        if len(data) > 0:
            returns = data['Adj Close'].pct_change().dropna()
            # Annualize
            annual_return = returns.mean() * 12
            annual_volatility = returns.std() * np.sqrt(12)
            print(f"Fetched Stats: Return={annual_return:.2%}, Volatility={annual_volatility:.2%}")
        else:
            raise ValueError("No data")
    except Exception as e:
        print(f"Could not fetch data ({e}), using defaults.")
        # UI shows 11.95% return and 16.38% volatility
        annual_return = 0.1195 
        annual_volatility = 0.1638
        print(f"Using UI Parameters: Return={annual_return:.2%}, Volatility={annual_volatility:.2%}")
    
    # Force UI parameters to ensure comparison matches
    annual_return = 0.1195
    annual_volatility = 0.1638

    # For this specific ETF (Vanguard FTSE All-World), historically around 8-9%.
    # If fetch fails, I'll use 8.5% and 15% as reasonable baseline.
    
    portfolio = [
        PortfolioETF(
            isin="IE00BK5BQT80",
            allocation=1.0,
            annual_return=float(annual_return), # Ensure float
            annual_volatility=float(annual_volatility)
        )
    ]
    
    # Setup Simulation
    years = list(range(start_year, end_year + 1))
    
    print(f"\nSimulation Parameters:")
    print(f"Period: {start_year} (Month {start_month}) - {end_year} ({len(years)} years)")
    print(f"Initial Capital: €{initial_capital:,.2f}")
    print(f"Initial Loan: €{initial_loan:,.2f}")
    print(f"Monthly Contribution: €{total_monthly:,.2f}")
    
    # Loan Calculation (Deterministic)
    starting_loans = {
        "Adult1": 83000, # Assigning all to one for simplicity or split?
        # User said "Alglaen 83000". Doesn't specify split. 
        # Loan evolution sums it up anyway.
        "Adult2": 0, "Laps1": 0, "Laps2": 0
    }
    
    # We must use calculate_loan_evolution logic
    loan_evolution = calculate_loan_evolution(
        starting_loans=starting_loans,
        contributions=contribs,
        years=years,
        rental=None,
        start_month=start_month
    )
    
    final_idx = -1
    total_loan_end = sum(loan_evolution[p][final_idx] for p in loan_evolution)
    
    print(f"\nCalculated Total Loan at end of {end_year}: €{total_loan_end:,.2f}")
    
    # Monte Carlo
    print("Running Monte Carlo (10,000 runs)...")
    ms = MonteCarloSimulator(
        portfolio=portfolio,
        contributions=contribs,
        rental=None,
        n_simulations=10000,
        seed=42 # Fixed seed for reproducibility
    )
    
    result = ms.simulate(
        start_year=start_year,
        end_year=end_year,
        starting_capital=initial_capital,
        start_month=start_month
    )
    
    # Extract Percentiles
    # Result has .percentiles dict
    
    scenarios = [10, 30, 50, 70]
    
    print(f"\nResults ({end_year}):")
    print(f"{'Scenario':<10} | {'Balance':<15} | {'Total Loan':<15} | {'Profit':<15}")
    print("-" * 65)
    
    for p in scenarios:
        key = f'p{p}'
        balance = result.percentiles[key][final_idx]
        profit = balance - total_loan_end
        print(f"{key.upper():<10} | €{balance:,.2f}    | €{total_loan_end:,.2f}    | €{profit:,.2f}")

    print("-" * 65)
    
    # Double check loan calculation manually
    # Year 1 (2026): 9 months (Apr-Dec). 9 * 1100 = 9900.
    # Years 2027-2035 (9 years). 9 * 12 * 1100 = 118800.
    # Total Contrib: 128700.
    # Initial: 83000.
    # Total: 211700.
    
    print(f"\nManual Loan Check:")
    print(f"2026 (Apr-Dec, 9m): 9 * 1100 = 9900")
    print(f"2027-2035 (9y): 9 * 12 * 1100 = 118800")
    print(f"Initial: 83000")
    print(f"Total: {83000 + 9900 + 118800}")
    
    assert abs(total_loan_end - 211700) < 1.0, f"Mismatch in loan calculation! Got {total_loan_end}"
    print("Loan calculation verified.")

if __name__ == "__main__":
    run_verification()
