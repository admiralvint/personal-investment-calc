"""
Unit tests for OÜ Investment Model.

Tests critical financial calculations to ensure accuracy.
"""

import pytest
import pandas as pd

from oyliivinvest import (
    OUInvestmentModel,
    InvestmentConfig,
    InvestmentConstants,
    AccountInfo,
)


class TestInvestmentConstants:
    """Test the constants are set correctly."""
    
    def test_tax_rate(self) -> None:
        """Tax rate should be 22%."""
        assert InvestmentConstants.INCOME_TAX_RATE == 0.22
    
    def test_valid_scenarios(self) -> None:
        """Valid scenarios should include HEA, KESKMINE, HALB."""
        assert 'HEA' in InvestmentConstants.VALID_SCENARIOS
        assert 'KESKMINE' in InvestmentConstants.VALID_SCENARIOS
        assert 'HALB' in InvestmentConstants.VALID_SCENARIOS
        assert len(InvestmentConstants.VALID_SCENARIOS) == 3
    
    def test_year_range(self) -> None:
        """Year range should be 2026-2040."""
        assert InvestmentConstants.START_YEAR == 2026
        assert InvestmentConstants.END_YEAR == 2040


class TestInvestmentConfig:
    """Test the configuration dataclass."""
    
    def test_default_accounts(self) -> None:
        """Default config should have 4 accounts with correct names."""
        config = InvestmentConfig()
        assert 'Laps1' in config.kontod
        assert 'Laps2' in config.kontod
        assert 'Mart' in config.kontod
        assert 'Kerli' in config.kontod
    
    def test_account_values(self) -> None:
        """Account values should match expected defaults."""
        config = InvestmentConfig()
        assert config.kontod['Laps1'].summa == 21000
        assert config.kontod['Laps1'].kasum == 5100
        assert config.kontod['Kerli'].summa == 30000
    
    def test_contribution_scenarios(self) -> None:
        """Contribution scenarios should have correct structure."""
        config = InvestmentConfig()
        for scenario in InvestmentConstants.VALID_SCENARIOS:
            assert scenario in config.sissemaksed
            contributions = config.sissemaksed[scenario]
            assert 'Mart' in contributions
            assert 'Kerli' in contributions
            assert 'Laps1' in contributions
            assert 'Laps2' in contributions


class TestOUInvestmentModel:
    """Test the investment model calculations."""
    
    @pytest.fixture
    def model(self) -> OUInvestmentModel:
        """Create a model instance for testing."""
        # Suppress print output during tests
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        sys.stdout = old_stdout
        return model
    
    def test_total_sum_calculation(self, model: OUInvestmentModel) -> None:
        """Total sum should be sum of all account balances."""
        expected = 21000 + 17000 + 19000 + 30000  # 87000
        assert model.kogusumma == expected
    
    def test_total_profit_calculation(self, model: OUInvestmentModel) -> None:
        """Total profit should be sum of all account profits."""
        expected = 5100 + 5000 + 1200 + 2500  # 13800
        assert model.kogukasum == expected
    
    def test_exit_tax_calculation(self, model: OUInvestmentModel) -> None:
        """Exit tax should be 22% of total profit."""
        expected = 13800 * 0.22  # 3036
        assert abs(model.valjumismaks_summa - expected) < 0.01
    
    def test_total_costs(self, model: OUInvestmentModel) -> None:
        """Total costs should be exit tax + setup costs."""
        expected = (13800 * 0.22) + 1000  # 4036
        assert abs(model.kogukulud - expected) < 0.01
    
    def test_starting_capital(self, model: OUInvestmentModel) -> None:
        """Starting capital should be total sum minus costs."""
        expected = 87000 - 4036  # 82964
        assert abs(model.algkapital - expected) < 1
    
    def test_loan_total_matches_capital(self, model: OUInvestmentModel) -> None:
        """Sum of all loans should approximately equal starting capital.
        
        Note: Model uses 100€ tolerance for loan adjustments internally.
        """
        loan_total = sum(model.alglaenud.values())
        # Match the model's internal tolerance (100€)
        assert abs(loan_total - model.algkapital) < 100


class TestMortgageCalculation:
    """Test mortgage balance calculations."""
    
    @pytest.fixture
    def model(self) -> OUInvestmentModel:
        """Create a model instance for testing."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        sys.stdout = old_stdout
        return model
    
    def test_mortgage_2026(self, model: OUInvestmentModel) -> None:
        """Mortgage at start of 2026 should be initial value."""
        balance = model.arvuta_uuri_hypoteek(2026)
        expected = 142635
        assert abs(balance - expected) < 1
    
    def test_mortgage_decreases_over_time(self, model: OUInvestmentModel) -> None:
        """Mortgage should decrease each year."""
        balance_2026 = model.arvuta_uuri_hypoteek(2026)
        balance_2030 = model.arvuta_uuri_hypoteek(2030)
        balance_2035 = model.arvuta_uuri_hypoteek(2035)
        
        assert balance_2030 < balance_2026
        assert balance_2035 < balance_2030
    
    def test_mortgage_before_start_is_zero(self, model: OUInvestmentModel) -> None:
        """Mortgage before 2026 should return 0."""
        assert model.arvuta_uuri_hypoteek(2020) == 0
        assert model.arvuta_uuri_hypoteek(2025) == 0


class TestScenarioValidation:
    """Test input validation."""
    
    @pytest.fixture
    def model(self) -> OUInvestmentModel:
        """Create a model instance for testing."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        sys.stdout = old_stdout
        return model
    
    def test_valid_scenario(self, model: OUInvestmentModel) -> None:
        """Valid scenarios should not raise errors."""
        # Should not raise
        df = model.arvuta_stsenaarium('KESKMINE', 'KESKMINE')
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 15  # 2026-2040 = 15 years
    
    def test_invalid_contribution_scenario(self, model: OUInvestmentModel) -> None:
        """Invalid contribution scenario should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid contribution"):
            model.arvuta_stsenaarium('INVALID', 'KESKMINE')
    
    def test_invalid_return_scenario(self, model: OUInvestmentModel) -> None:
        """Invalid return scenario should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid return"):
            model.arvuta_stsenaarium('KESKMINE', 'INVALID')


class TestScenarioOutput:
    """Test scenario output structure."""
    
    @pytest.fixture
    def model(self) -> OUInvestmentModel:
        """Create a model instance for testing."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        sys.stdout = old_stdout
        return model
    
    def test_scenario_dataframe_columns(self, model: OUInvestmentModel) -> None:
        """Scenario output should have expected columns."""
        df = model.arvuta_stsenaarium('KESKMINE', 'KESKMINE')
        
        required_columns = [
            'Aasta', 'Algbilanss', 'Loppbilanss', 
            'Kogulaaen_Lopp', 'Kasumid', 'Investeerimiskasum'
        ]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
    
    def test_scenario_year_range(self, model: OUInvestmentModel) -> None:
        """Scenario should cover 2026-2040."""
        df = model.arvuta_stsenaarium('HEA', 'HEA')
        
        years = df['Aasta'].tolist()
        assert years[0] == 2026
        assert years[-1] == 2040
        assert len(years) == 15
    
    def test_balance_increases_over_time(self, model: OUInvestmentModel) -> None:
        """Balance should generally increase over time (with positive returns)."""
        df = model.arvuta_stsenaarium('HEA', 'HEA')
        
        balance_2026 = df[df['Aasta'] == 2026]['Loppbilanss'].values[0]
        balance_2040 = df[df['Aasta'] == 2040]['Loppbilanss'].values[0]
        
        assert balance_2040 > balance_2026
    
    def test_repayment_year_reduces_balance(self, model: OUInvestmentModel) -> None:
        """2030 repayment should reduce balance compared to normal growth."""
        df = model.arvuta_stsenaarium('KESKMINE', 'KESKMINE')
        
        # Check repayment happened in 2030
        row_2030 = df[df['Aasta'] == 2030].iloc[0]
        repayment = row_2030['Uuri_Tagasimakse']
        
        expected_repayment = 54662.5 + 54662.5  # Mart + Kerli
        assert abs(repayment - expected_repayment) < 1


class TestAllScenarios:
    """Test running all scenarios."""
    
    @pytest.fixture
    def model(self) -> OUInvestmentModel:
        """Create a model instance for testing."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        sys.stdout = old_stdout
        return model
    
    def test_all_scenarios_count(self, model: OUInvestmentModel) -> None:
        """Should generate 9 scenarios (3x3 matrix)."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        results = model.arvuta_koik_stsenaariumid()
        sys.stdout = old_stdout
        
        assert len(results) == 9
    
    def test_all_scenarios_naming(self, model: OUInvestmentModel) -> None:
        """All scenario names should follow pattern."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        results = model.arvuta_koik_stsenaariumid()
        sys.stdout = old_stdout
        
        expected_names = [
            'HEA_HEA', 'HEA_KESKMINE', 'HEA_HALB',
            'KESKMINE_HEA', 'KESKMINE_KESKMINE', 'KESKMINE_HALB',
            'HALB_HEA', 'HALB_KESKMINE', 'HALB_HALB'
        ]
        
        for name in expected_names:
            assert name in results, f"Missing scenario: {name}"


class TestSummaryGeneration:
    """Test summary table generation."""
    
    @pytest.fixture
    def model_with_results(self) -> tuple[OUInvestmentModel, dict]:
        """Create model and run scenarios."""
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        model = OUInvestmentModel()
        results = model.arvuta_koik_stsenaariumid()
        sys.stdout = old_stdout
        return model, results
    
    def test_summary_row_count(self, model_with_results: tuple) -> None:
        """Summary should have one row per scenario."""
        model, results = model_with_results
        summary = model.loo_kokkuvote(results)
        
        assert len(summary) == 9
    
    def test_loan_summary_structure(self, model_with_results: tuple) -> None:
        """Loan summary should have correct columns."""
        model, results = model_with_results
        loan_summary = model.loo_laenude_detailne_kokkuvote(results)
        
        assert 'Stsenaarium' in loan_summary.columns
        assert '2030_Mart' in loan_summary.columns
        assert '2040_Laps2' in loan_summary.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
