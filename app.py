"""
Flask Web Application for Personal Investment Account Modeler.
(Estonian Investeerimiskonto System - Multi-Asset Version)
"""

from flask import Flask, render_template, request, jsonify
from etf_fetcher import fetch_etf_data
from monte_carlo import MonteCarloSimulator, AssetParams

app = Flask(__name__)

# Default config
DEFAULT_CONFIG = {
    'assets': [
        {'isin': 'TNESCFD', 'value': 2000},
        {'isin': 'IE00BK5BQT80', 'value': 10000},
    ],
    'strategy': [
        {'isin': 'IE00BK5BQT80', 'amount': 800},
        {'isin': 'IE00BKM4GZ66', 'amount': 200} # EMIM
    ],
    'annual_costs': 50,
    'start_year': 2026,
    'end_year': 2040
}

@app.route('/')
def index():
    return render_template('index.html', config=DEFAULT_CONFIG)

@app.route('/api/etf/<isin>')
def get_etf_info(isin: str):
    data = fetch_etf_data(isin)
    if data:
        return jsonify({'success': True, 'data': data.to_dict()})
    return jsonify({'success': False, 'error': f'ETF not found: {isin}'})

@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    try:
        params = request.json
        
        # 1. Parse Current Assets
        assets_input = params.get('assets', [])
        current_assets = {} # ISIN -> Value
        
        for item in assets_input:
            isin = item.get('isin', '').strip()
            val = float(item.get('value', 0))
            if isin and val >= 0:
                current_assets[isin] = current_assets.get(isin, 0) + val
                
        # 2. Parse Monthly Strategy
        strategy_input = params.get('strategy', [])
        monthly_allocations = {} # ISIN -> Amount
        
        for item in strategy_input:
            isin = item.get('isin', '').strip()
            amt = float(item.get('amount', 0))
            if isin and amt > 0:
                monthly_allocations[isin] = monthly_allocations.get(isin, 0) + amt
        
        # 3. Fetch Data for ALL ISINs
        all_isins = set(current_assets.keys()) | set(monthly_allocations.keys())
        asset_params_map = {}
        etf_info = []
        
        for isin in all_isins:
            data = fetch_etf_data(isin)
            if not data:
                return jsonify({'success': False, 'error': f'Could not fetch data for {isin}'})
            
            asset_params_map[isin] = AssetParams(
                isin=isin,
                annual_return=data.annual_return,
                annual_volatility=data.annual_volatility
            )
            etf_info.append(data.to_dict())

        # 4. Simulation Setup
        annual_costs = float(params.get('annual_costs', 0))
        withdrawal_rate = float(params.get('withdrawal_rate', 0)) / 100
        withdrawal_start = int(params.get('withdrawal_start_year', 2035))
        
        start_year = int(params.get('start_year', 2026))
        end_year = int(params.get('end_year', 2040))
        
        simulator = MonteCarloSimulator(
            asset_params=asset_params_map,
            n_simulations=5000
        )
        
        result = simulator.simulate(
            current_assets=current_assets,
            monthly_allocations=monthly_allocations,
            start_year=start_year,
            end_year=end_year,
            annual_costs=annual_costs,
            withdrawal_rate=withdrawal_rate,
            withdrawal_start_year=withdrawal_start,
            contribution_end_year=int(params['contribution_end_year']) if params.get('contribution_end_year') else None
        )
        
        # 5. Build Result Breakdown (Dynamic on Frontend now)
        # We pass monthly_total_contrib to help frontend calc
        monthly_total_contrib = sum(monthly_allocations.values())
        starting_capital = sum(current_assets.values())

        return jsonify({
            'success': True,
            'simulation': result.to_dict(),
            'monthly_total_contrib': monthly_total_contrib,
            'etf_info': etf_info,
            'starting_capital': starting_capital
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})

if __name__ == '__main__':
    print("Personal Investment Modeler running on port 5022")
    app.run(debug=True, port=5022)
