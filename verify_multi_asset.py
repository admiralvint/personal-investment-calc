from monte_carlo import MonteCarloSimulator, AssetParams

def test_multi_asset():
    print("Testing Multi-Asset Logic...")
    
    # Setup Params
    params_map = {
        'OLD': AssetParams('OLD', 0.10, 0.0), # 10% return
        'NEW': AssetParams('NEW', 0.10, 0.0)  # 10% return
    }
    
    sim = MonteCarloSimulator(params_map, n_simulations=1, seed=42)
    
    # Scenario:
    # OLD: 1000 start, 0 contrib. -> 1000 * 1.1 = 1100 (Year 1)
    # NEW: 0 start, 100/mo contrib. -> 1200 + growth (~60) = 1260
    # Total Invested: 1000 + 1200 = 2200.
    
    res = sim.simulate(
        current_assets={'OLD': 1000.0},
        monthly_allocations={'NEW': 100.0},
        start_year=2026,
        end_year=2026, # 1 Year
        annual_costs=0,
        withdrawal_rate=0
    )
    
    final_balance = res.p50[0]
    final_invested = res.deposit_pot_p50[0]
    
    print(f"Final Balance: {final_balance}")
    print(f"Final Invested: {final_invested}")
    
    # Check Invested
    # 1000 + 12*100 = 2200
    if abs(final_invested - 2200) < 0.1:
        print("PASS: Invested Amount Correct (2200)")
    else:
        print(f"FAIL: Invested {final_invested} != 2200")
        
    # Check Balance
    # OLD: 1000 -> grows at ~10% (monthly compounded)
    # NEW: 100/mo.
    # Theoretical approx check
    expected_min = 2200
    # 10% growth on 1000 = 100
    # 10% growth on avg 600 (new money) = 60
    # Total gain ~160. Total ~2360.
    if final_balance > 2300 and final_balance < 2400:
        print(f"PASS: Balance {final_balance} in expected range (2300-2400)")
    else:
        print(f"FAIL/WARN: Balance {final_balance} outside range (check return logic)")

if __name__ == "__main__":
    test_multi_asset()
