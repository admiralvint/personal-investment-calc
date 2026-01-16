"""
Monte Carlo Simulation Engine for Personal Investment Account (Multi-Asset).
"""

from dataclasses import dataclass
from typing import Optional, Dict

import numpy as np


@dataclass
class SimulationResult:
    """Container for Monte Carlo simulation results."""
    years: list[int]
    percentiles: Dict[int, list[float]] # p1..p99
    
    # New: Breakdown Stats per Percentile
    payouts_percentiles: Dict[int, list[float]]
    taxes_percentiles: Dict[int, list[float]]
    costs_percentiles: Dict[int, list[float]]

    # Restored legacy fields for compatibility
    p10: list[float]
    p50: list[float]
    p90: list[float]
    
    mean: list[float]
    deposit_pot_p50: list[float]
    
    def to_dict(self) -> dict:
        return {
            'years': self.years,
            'percentiles': {k: [round(v, 2) for v in vals] for k, vals in self.percentiles.items()},
            # Explicitly include p10/p50/p90 in dict for frontend legacy parts if any
            'p10': [round(v, 2) for v in self.percentiles[10]], 
            'p50': [round(v, 2) for v in self.percentiles[50]],
            'p90': [round(v, 2) for v in self.percentiles[90]],
            'mean': [round(v, 2) for v in self.mean],
            
            # Full Payout/Tax Maps (Key: Percentile 1-99, Value: List[float])
            'payouts_percentiles': {k: [round(v, 2) for v in vals] for k, vals in self.payouts_percentiles.items()},
            'taxes_percentiles': {k: [round(v, 2) for v in vals] for k, vals in self.taxes_percentiles.items()},
            'costs_percentiles': {k: [round(v, 2) for v in vals] for k, vals in self.costs_percentiles.items()},
            'deposit_pot_p50': [round(v, 2) for v in self.deposit_pot_p50]
        }


@dataclass
class AssetParams:
    """Return/Volatility parameters for an asset."""
    isin: str
    annual_return: float
    annual_volatility: float


class MonteCarloSimulator:
    """Monte Carlo simulation engine (Multi-Asset)."""
    
    def __init__(
        self,
        asset_params: Dict[str, AssetParams],
        n_simulations: int = 5000,
        seed: Optional[int] = None
    ):
        self.asset_params = asset_params
        self.n_simulations = n_simulations
        
        if seed is not None:
            np.random.seed(seed)
            
    def simulate(
        self,
        current_assets: Dict[str, float], # ISIN -> Current Value
        monthly_allocations: Dict[str, float], # ISIN -> Monthly Contribution
        start_year: int = 2026,
        end_year: int = 2040,
        annual_costs: float = 0.0,
        withdrawal_rate: float = 0.0,
        withdrawal_start_year: int = 2035,
        contribution_end_year: Optional[int] = None
    ) -> SimulationResult:
        years = list(range(start_year, end_year + 1))
        n_years = len(years)
        
        # Determine total starting capital
        starting_capital = sum(current_assets.values())
        
        # Prepare arrays
        paths = np.zeros((self.n_simulations, n_years))
        payouts_paths = np.zeros((self.n_simulations, n_years))
        taxes_paths = np.zeros((self.n_simulations, n_years))
        costs_paths = np.zeros((self.n_simulations, n_years))
        deposit_pot_paths = np.zeros((self.n_simulations, n_years))
        
        # Pre-calc monthly params for each asset
        asset_monthly_params = {}
        all_isins = set(current_assets.keys()) | set(monthly_allocations.keys())
        
        for isin in all_isins:
            params = self.asset_params.get(isin)
            if params:
                asset_monthly_params[isin] = {
                    'mu': params.annual_return / 12,
                    'sigma': params.annual_volatility / np.sqrt(12)
                }
            else:
                asset_monthly_params[isin] = {'mu': 0.0, 'sigma': 0.0}
        
        TAX_RATE = 0.22
        
        for sim in range(self.n_simulations):
            # Track separate balances for this simulation run
            sim_balances = current_assets.copy()
            # Ensure all future assets are in dict
            for isin in monthly_allocations:
                if isin not in sim_balances:
                    sim_balances[isin] = 0.0
            
            total_invested = starting_capital
            total_withdrawn = 0.0
            
            for year_idx, year in enumerate(years):
                
                # Determine Withdrawal Budget
                current_total_balance = sum(sim_balances.values())
                withdrawal_budget = 0.0
                if year >= withdrawal_start_year and withdrawal_rate > 0:
                    withdrawal_budget = current_total_balance * withdrawal_rate
                
                year_net_payout = 0.0
                year_tax = 0.0
                year_costs = 0.0
                
                for month in range(12):
                    # 1. Contributions
                    # Stop contributions if current year >= contribution_end_year (Coast FIRE)
                    is_contributing = True
                    if contribution_end_year is not None and year >= contribution_end_year:
                        is_contributing = False

                    if is_contributing:
                        for isin, amount in monthly_allocations.items():
                            sim_balances[isin] += amount
                            total_invested += amount
                    
                    # 2. Costs (Proportional Deduction)
                    total_bal = sum(sim_balances.values())
                    if total_bal > 0 and annual_costs > 0:
                        monthly_cost = annual_costs / 12
                        # Cap cost at total balance
                        if monthly_cost > total_bal:
                            monthly_cost = total_bal
                        
                        year_costs += monthly_cost
                        cost_factor = max(0.0, 1.0 - (monthly_cost / total_bal))
                        for isin in sim_balances:
                            sim_balances[isin] *= cost_factor
                    
                    # 3. Withdrawals (Proportional)
                    if withdrawal_budget > 0:
                        monthly_wd = withdrawal_budget / 12
                        total_bal = sum(sim_balances.values())
                        
                        if total_bal >= monthly_wd:
                            prev_excess = max(0.0, total_withdrawn - total_invested)
                            new_excess = max(0.0, (total_withdrawn + monthly_wd) - total_invested)
                            incremental_taxable = new_excess - prev_excess
                            
                            tax = incremental_taxable * TAX_RATE
                            net = monthly_wd - tax
                            
                            year_net_payout += net
                            year_tax += tax
                            total_withdrawn += monthly_wd
                            
                            wd_factor = max(0.0, 1.0 - (monthly_wd / total_bal))
                            for isin in sim_balances:
                                sim_balances[isin] *= wd_factor
                                
                    # 4. Market Return
                    for isin in sim_balances:
                        if sim_balances[isin] > 0:
                            params = asset_monthly_params[isin]
                            ret = np.random.normal(params['mu'], params['sigma'])
                            sim_balances[isin] *= (1 + ret)
                
                # End Year Record
                paths[sim, year_idx] = sum(sim_balances.values())
                payouts_paths[sim, year_idx] = year_net_payout
                taxes_paths[sim, year_idx] = year_tax
                costs_paths[sim, year_idx] = year_costs
                deposit_pot_paths[sim, year_idx] = total_invested
                
        # Aggregation: Percentiles 1 to 99
        mean = np.mean(paths, axis=0).tolist()
        
        # Optimize calculating 99 percentiles
        percentile_values = np.percentile(paths, np.arange(1, 100), axis=0) # Shape (99, n_years)
        payouts_values = np.percentile(payouts_paths, np.arange(1, 100), axis=0)
        taxes_values = np.percentile(taxes_paths, np.arange(1, 100), axis=0)
        costs_values = np.percentile(costs_paths, np.arange(1, 100), axis=0)
        
        percentiles_dict = {}
        payouts_dict = {}
        taxes_dict = {}
        costs_dict = {}
        
        for i in range(1, 100):
            percentiles_dict[i] = percentile_values[i-1].tolist()
            payouts_dict[i] = payouts_values[i-1].tolist()
            taxes_dict[i] = taxes_values[i-1].tolist()
            costs_dict[i] = costs_values[i-1].tolist()
            
        deposit_pot_p50 = np.percentile(deposit_pot_paths, 50, axis=0).tolist()
        
        return SimulationResult(
            years=years,
            percentiles=percentiles_dict,
            payouts_percentiles=payouts_dict,
            taxes_percentiles=taxes_dict,
            costs_percentiles=costs_dict,
            
            # Populate legacy fields from dict
            p10=percentiles_dict[10],
            p50=percentiles_dict[50],
            p90=percentiles_dict[90],
            mean=mean,
            deposit_pot_p50=deposit_pot_p50
        )
