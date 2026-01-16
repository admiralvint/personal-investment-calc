import numpy as np
from monte_carlo import MonteCarloSimulator, PortfolioETF, Contribution

def test_tax_logic():
    print("Testing Investment Account Tax Logic...")
    
    # 1. Setup deterministic portfolio (10% return, 0% vol)
    portfolio = [PortfolioETF("TEST", 1.0, 0.10, 0.0)]
    
    # 2. Case: Withdrawal exceeds contributions
    # Start: 1000
    # Growth: 10% -> 1100
    # Withdraw: 1050
    # Taxable: 50
    # Tax: 50 * 0.22 = 11
    # Net: 1039
    
    sim = MonteCarloSimulator(portfolio, contributions=0, n_simulations=1, seed=42)
    # Force daily return to be exactly annual_return / 252 (or just use monthly model)
    # Simulator uses monthly: monthly_return = 0.10/12 = 0.00833
    # Balance after 12 months = 1000 * (1+0.00833)^12 ~= 1000 * (1.104) 
    # Actually (1+r/12)^12 approx 1+r.
    
    # Let's run simulate
    res = sim.simulate(
        start_year=2026,
        end_year=2026,
        starting_capital=1000.0,
        annual_costs=0,
        withdrawal_rate=1.05, # 105% of start? No, rate is % of CURRENT balance.
        withdrawal_start_year=2026
    )
    # If I set withdrawal_rate to ensure 1050 withdrawal.
    # It's hard to hit exactly 1050 with rate.
    
    # Let's just create a mock scenario by modifying simulate or trust logical flow.
    # Or I can use "withdrawal_rate" carefully.
    
    # Check "Deposit Pot" logic.
    # Year 2026.
    # Invested: 1000.
    # Withdrawn: Payouts (Net) + Tax.
    
    payout = res.payouts_p50[0]
    tax = res.tax_paid_p50[0]
    pot = res.deposit_pot_p50[0]
    
    print(f"Payout: {payout}")
    print(f"Tax: {tax}")
    print(f"Pot: {pot}")
    
    # If logic works, Tax should be > 0 IF Payout+Tax > 1000.
    total_gross_wd = payout + tax
    print(f"Total Gross WD: {total_gross_wd}")
    
    if total_gross_wd > 1000:
        expected_tax = (total_gross_wd - 1000) * 0.22
        print(f"Expected Tax (approx): {expected_tax}")
        if abs(tax - expected_tax) < 1.0:
            print("PASS: Tax calculation seems correct.")
        else:
            print("FAIL: Tax mismatch.")
    else:
        print("Note: Withdrawal did not exceed deposit, so Tax should be 0.")
        if tax == 0:
            print("PASS: No tax paid as expected.")
        else:
            print(f"FAIL: Tax paid {tax} unexpectedly.")

if __name__ == "__main__":
    test_tax_logic()
