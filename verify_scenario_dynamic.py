
import numpy as np

def run_dynamic_verification():
    # Parameters
    start_year = 2026
    start_month = 4
    end_year = 2035
    initial_capital = 83000.0
    initial_loan = 83000.0
    
    annual_return = 0.088
    monthly_return = annual_return / 12
    
    # Contribution Schedule
    # Until 2030 (inclusive): 2100
    # After 2030: 600
    
    current_balance = initial_capital
    total_loan = initial_loan
    
    print(f"Simulation Period: {start_year} (Month {start_month}) to {end_year}")
    print(f"Initial: €{initial_capital:,.2f}")
    print(f"Return: {annual_return:.1%}")
    print("-" * 40)
    
    for year in range(start_year, end_year + 1):
        # Determine montly contribution for this year
        if year <= 2030:
            monthly_contrib = 2100.0
        else:
            monthly_contrib = 600.0
            
        start_m = start_month if year == start_year else 1
        months_in_year = 12 - start_m + 1
        
        # Simulate months
        year_contribs = 0
        for _ in range(months_in_year):
            # Add contribution (Beginning of month? App does balance += contrib, then return)
            current_balance += monthly_contrib
            total_loan += monthly_contrib
            year_contribs += monthly_contrib
            
            # Apply return
            current_balance *= (1 + monthly_return)
            
        print(f"Year {year}: Contrib €{monthly_contrib:,.0f}/mo. Year Total: €{year_contribs:,.0f}. End Bal: €{current_balance:,.2f}")

    print("-" * 40)
    print(f"Final Balance (2035): €{current_balance:,.2f}")
    print(f"Total Loan Input:     €{total_loan:,.2f}")
    print(f"Actual Profit:        €{current_balance - total_loan:,.2f}")

if __name__ == "__main__":
    run_dynamic_verification()
