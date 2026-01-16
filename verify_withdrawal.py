
def run_withdrawal_verification():
    # Phase 1 Result
    start_balance_2036 = 471502.70
    
    # Phase 2 Parameters
    start_year = 2036
    end_year = 2050
    annual_withdrawal = 25000.0
    monthly_withdrawal = annual_withdrawal / 12
    annual_return = 0.088
    monthly_return = annual_return / 12  # Simplified monthly compounding
    
    current_balance = start_balance_2036
    
    print(f"Phase 2 Period: {start_year}-{end_year}")
    print(f"Start Balance: €{start_balance_2036:,.2f}")
    print(f"Annual Withdrawal: €{annual_withdrawal:,.2f} (€{monthly_withdrawal:,.2f}/mo)")
    print(f"Growth: {annual_return:.1%}")
    print("-" * 65)
    print(f"{'Year':<6} | {'Start Bal':<15} | {'Growth':<12} | {'Withdrawal':<12} | {'End Bal':<15}")
    print("-" * 65)
    
    for year in range(start_year, end_year + 1):
        year_start = current_balance
        year_growth = 0
        year_withdrawn = 0
        
        for month in range(12):
            # 1. Apply Withdraw (Assumption: Needed for living, taken at start or during month)
            # Or Apply Growth then Withdraw? 
            # Standard: Start Bal -> Growth -> Withdraw (End of month)
            # Or Start Bal -> Withdraw -> Growth (Start of month)
            # Let's assume End of Month withdrawal to be optimistic/standard salary logic.
            
            # Growth
            growth = current_balance * monthly_return
            current_balance += growth
            year_growth += growth
            
            # Withdraw
            current_balance -= monthly_withdrawal
            year_withdrawn += monthly_withdrawal
            
        print(f"{year:<6} | €{year_start:,.0f}        | +€{year_growth:,.0f}      | -€{year_withdrawn:,.0f}      | €{current_balance:,.0f}")

    print("-" * 65)
    print(f"Final Balance (2050): €{current_balance:,.2f}")

if __name__ == "__main__":
    run_withdrawal_verification()
