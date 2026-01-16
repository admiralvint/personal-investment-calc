"""
OÜ Investment Model - Estonian Limited Liability Company Investment Simulator

This model projects investment scenarios for transferring personal investment accounts
into an Estonian OÜ structure, tracking capital, loans, returns, and rental property.
"""

import argparse
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class InvestmentConstants:
    """Constants used throughout the investment model."""
    
    # Tax rates
    INCOME_TAX_RATE: float = 0.22
    
    # Setup costs
    SETUP_COST_EUR: float = 1000.0
    
    # Mortgage parameters
    MORTGAGE_INTEREST_RATE: float = 0.04
    MONTHS_PER_YEAR: int = 12
    
    # Valid scenario names
    VALID_SCENARIOS: tuple = ('HEA', 'KESKMINE', 'HALB')
    
    # Projection years
    START_YEAR: int = 2026
    END_YEAR: int = 2040


@dataclass
class AccountInfo:
    """Investment account information."""
    summa: float
    kasum: float


@dataclass 
class InvestmentConfig:
    """Configuration for the investment model."""
    
    # Account balances - using Laps1/Laps2 consistently
    kontod: dict[str, AccountInfo] = field(default_factory=lambda: {
        'Laps1': AccountInfo(summa=21000, kasum=5100),
        'Laps2': AccountInfo(summa=17000, kasum=5000),
        'Mart': AccountInfo(summa=19000, kasum=1200),
        'Kerli': AccountInfo(summa=30000, kasum=2500)
    })
    
    # Initial monthly contribution (Jan-Nov 2026)
    algne_kuu: float = 2000.0
    
    # Monthly contributions by scenario (Dec 2026+)
    sissemaksed: dict[str, dict[str, float]] = field(default_factory=lambda: {
        'HEA': {'Mart': 1000, 'Kerli': 1000, 'Laps1': 150, 'Laps2': 150},
        'KESKMINE': {'Mart': 850, 'Kerli': 850, 'Laps1': 150, 'Laps2': 150},
        'HALB': {'Mart': 1000, 'Kerli': 200, 'Laps1': 150, 'Laps2': 150}
    })
    
    # Return scenarios (annual percentage)
    tootlused: dict[str, float] = field(default_factory=lambda: {
        'HEA': 0.10,
        'KESKMINE': 0.08,
        'HALB': 0.05
    })
    
    # Rental property parameters
    uuri_hypoteek_2026: float = 142635.0
    uuri_igakuine_makse: float = 760.0
    uuri_tulu_bruto: float = 1100.0
    uuri_maks: float = 194.0
    uuri_hooldus: float = 11.0
    uuri_neto: float = 1089.0  # Net income to OÜ after expenses
    
    # Repayment plan (Mart and Kerli 50/50)
    tagasimakse_aasta: int = 2030
    mart_tagasimakse: float = 54662.5
    kerli_tagasimakse: float = 54662.5


class OUInvestmentModel:
    """OÜ Investment Model for Estonian company structure."""
    
    def __init__(self, config: Optional[InvestmentConfig] = None) -> None:
        """
        Initialize the investment model.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or InvestmentConfig()
        self._initialize_calculations()
        self.prindi_algandmed()
    
    def _initialize_calculations(self) -> None:
        """Initialize derived calculations from configuration."""
        # Total sums from accounts
        self.kogusumma = sum(
            acc.summa for acc in self.config.kontod.values()
        )
        self.kogukasum = sum(
            acc.kasum for acc in self.config.kontod.values()
        )
        
        # Taxes and costs
        self.valjumismaks_summa = self.kogukasum * InvestmentConstants.INCOME_TAX_RATE
        self.seadistuskulud = InvestmentConstants.SETUP_COST_EUR
        self.kogukulud = self.valjumismaks_summa + self.seadistuskulud
        
        # Net capital to OÜ
        self.algkapital = self.kogusumma - self.kogukulud
        
        # Initial loans distribution (proportional, simplified)
        # Each person's loan = their contribution minus their share of taxes/costs
        self.alglaenud = self._calculate_initial_loans()
        
        # Verify loans sum to starting capital
        self._verify_loan_totals()
    
    def _calculate_initial_loans(self) -> dict[str, float]:
        """Calculate initial loan amounts for each person."""
        # Approximate distribution based on original code
        return {
            'Mart': 18500.0,
            'Kerli': 29100.0,
            'Laps1': 19600.0,
            'Laps2': 15800.0
        }
    
    def _verify_loan_totals(self) -> None:
        """Verify loan totals match starting capital."""
        laenude_summa = sum(self.alglaenud.values())
        if abs(laenude_summa - self.algkapital) > 100:
            print(f"⚠️  HOIATUS: Laenude summa ({laenude_summa}) ei vasta algkapitalile ({self.algkapital})")
            # Adjust last loan to match
            vahe = self.algkapital - (laenude_summa - self.alglaenud['Laps2'])
            self.alglaenud['Laps2'] = vahe
            print(f"   Korrigeeritud Laps2 laen: {self.alglaenud['Laps2']}")
    
    def prindi_algandmed(self) -> None:
        """Print initial data for verification."""
        print("\n" + "="*80)
        print("ALGANDMED JA PARAMEETRID")
        print("="*80)
        
        print("\n📊 PRAEGUSED INVESTEERIMISKONTOD:")
        for isik, andmed in self.config.kontod.items():
            print(f"   {isik:8s}: €{andmed.summa:>7,} (kasum: €{andmed.kasum:>6,})")
        print(f"   {'KOKKU':8s}: €{self.kogusumma:>7,} (kasum: €{self.kogukasum:>6,})")
        
        print(f"\n💶 MAKSUD JA KULUD:")
        print(f"   Väljumismaks ({InvestmentConstants.INCOME_TAX_RATE*100:.0f}%):    €{self.valjumismaks_summa:>7,.2f}")
        print(f"   Seadistuskulud:        €{self.seadistuskulud:>7,.2f}")
        print(f"   KOKKU kulud:           €{self.kogukulud:>7,.2f}")
        
        print(f"\n💰 OÜ-SSE KANTAV:")
        print(f"   Algkapital:            €{self.algkapital:>7,.2f}")
        
        print(f"\n📝 ALGLAENUD OÜ-LE:")
        for isik, summa in self.alglaenud.items():
            protsent = (summa / self.algkapital) * 100
            print(f"   {isik:8s}: €{summa:>7,.2f} ({protsent:>5.2f}%)")
        print(f"   {'KOKKU':8s}: €{sum(self.alglaenud.values()):>7,.2f}")
        
        print(f"\n🏠 ÜÜRIKORTER:")
        print(f"   Hüpoteek 2026:         €{self.config.uuri_hypoteek_2026:>7,.2f}")
        print(f"   Igakuine makse:        €{self.config.uuri_igakuine_makse:>7,.2f}")
        print(f"   Intress (aastas):      {InvestmentConstants.MORTGAGE_INTEREST_RATE*100:>7.2f}%")
        print(f"   Üüritulu (bruto):      €{self.config.uuri_tulu_bruto:>7,.2f}/kuu")
        print(f"   Neto OÜ-le (pärast):   €{self.config.uuri_neto:>7,.2f}/kuu")
        
        print(f"\n📅 TAGASIMAKSE PLAAN:")
        print(f"   Aasta:                 {self.config.tagasimakse_aasta}")
        print(f"   Mart:                  €{self.config.mart_tagasimakse:>7,.2f}")
        print(f"   Kerli:                 €{self.config.kerli_tagasimakse:>7,.2f}")
        print(f"   KOKKU:                 €{self.config.mart_tagasimakse + self.config.kerli_tagasimakse:>7,.2f}")
        
        print("\n" + "="*80 + "\n")
    
    def arvuta_uuri_hypoteek(self, aasta: int) -> float:
        """
        Calculate mortgage balance for a given year.
        
        Args:
            aasta: The year to calculate balance for.
            
        Returns:
            Remaining mortgage balance.
        """
        if aasta < InvestmentConstants.START_YEAR:
            return 0.0
        
        kuud = (aasta - InvestmentConstants.START_YEAR) * InvestmentConstants.MONTHS_PER_YEAR
        bilanss = self.config.uuri_hypoteek_2026
        kuuintress = InvestmentConstants.MORTGAGE_INTEREST_RATE / InvestmentConstants.MONTHS_PER_YEAR
        
        for _ in range(kuud):
            if bilanss <= 0:
                break
            intress = bilanss * kuuintress
            pohiosa = self.config.uuri_igakuine_makse - intress
            bilanss -= pohiosa
            if bilanss < 0:
                bilanss = 0.0
        
        return bilanss
    
    def _validate_scenario(self, scenario: str, scenario_type: str) -> None:
        """
        Validate that a scenario name is valid.
        
        Args:
            scenario: The scenario name to validate.
            scenario_type: Description for error message.
            
        Raises:
            ValueError: If scenario is not valid.
        """
        if scenario not in InvestmentConstants.VALID_SCENARIOS:
            raise ValueError(
                f"Invalid {scenario_type} scenario: '{scenario}'. "
                f"Valid options: {InvestmentConstants.VALID_SCENARIOS}"
            )
    
    def arvuta_stsenaarium(
        self, 
        sissemakse_stsenaarium: str, 
        tootlus_stsenaarium: str
    ) -> pd.DataFrame:
        """
        Calculate projections for one scenario from 2026-2040.
        
        Args:
            sissemakse_stsenaarium: Contribution scenario ('HEA', 'KESKMINE', 'HALB')
            tootlus_stsenaarium: Return scenario ('HEA', 'KESKMINE', 'HALB')
            
        Returns:
            DataFrame with yearly projections.
            
        Raises:
            ValueError: If scenarios are not valid.
        """
        # Validate inputs
        self._validate_scenario(sissemakse_stsenaarium, "contribution (sissemakse)")
        self._validate_scenario(tootlus_stsenaarium, "return (tootlus)")
        
        sissemaksed = self.config.sissemaksed[sissemakse_stsenaarium]
        tootlus = self.config.tootlused[tootlus_stsenaarium]
        
        aastad = list(range(InvestmentConstants.START_YEAR, InvestmentConstants.END_YEAR + 1))
        tulemused = []
        
        # Starting balance
        eelmine_bilanss = self.algkapital
        eelmised_laenud = self.alglaenud.copy()
        
        for aasta in aastad:
            # Year start balance
            algbilanss = eelmine_bilanss
            alglaenud = eelmised_laenud.copy()
            kogulaaen_algus = sum(alglaenud.values())
            
            # Annual contributions
            if aasta == InvestmentConstants.START_YEAR:
                # 11 months initial (2000) + 1 month new (per scenario)
                aasta_sissemakse = (
                    self.config.algne_kuu * 11 + sum(sissemaksed.values()) * 1
                )
                # Loan additions proportionally
                kogusumma_kuu = sum(sissemaksed.values())
                laenu_lisad = {
                    isik: (self.config.algne_kuu / kogusumma_kuu * summa) * 11 + summa * 1
                    for isik, summa in sissemaksed.items()
                }
            else:
                aasta_sissemakse = sum(sissemaksed.values()) * InvestmentConstants.MONTHS_PER_YEAR
                laenu_lisad = {
                    isik: summa * InvestmentConstants.MONTHS_PER_YEAR 
                    for isik, summa in sissemaksed.items()
                }
            
            # Rental income to OÜ (only after repayment)
            if aasta > self.config.tagasimakse_aasta:
                uuri_tulu = self.config.uuri_neto * InvestmentConstants.MONTHS_PER_YEAR
            else:
                uuri_tulu = 0.0
            
            # Investment returns (average balance × return rate)
            keskmine_bilanss = algbilanss + aasta_sissemakse / 2 + uuri_tulu / 2
            investeerimiskasum = keskmine_bilanss * tootlus
            
            # Rental repayment
            if aasta == self.config.tagasimakse_aasta:
                uuri_tagasimakse = self.config.mart_tagasimakse + self.config.kerli_tagasimakse
                laenu_vahenemised = {
                    'Mart': self.config.mart_tagasimakse,
                    'Kerli': self.config.kerli_tagasimakse,
                    'Laps1': 0.0,
                    'Laps2': 0.0
                }
            else:
                uuri_tagasimakse = 0.0
                laenu_vahenemised = {isik: 0.0 for isik in sissemaksed.keys()}
            
            # Ending balance
            loppbilanss = (
                algbilanss + aasta_sissemakse + uuri_tulu + 
                investeerimiskasum - uuri_tagasimakse
            )
            
            # Ending loans
            lopp_laenud = {
                isik: alglaenud[isik] + laenu_lisad[isik] - laenu_vahenemised[isik]
                for isik in sissemaksed.keys()
            }
            kogulaaen_lopp = sum(lopp_laenud.values())
            
            # Profits
            kasumid = loppbilanss - kogulaaen_lopp
            
            # Save results
            tulemus = {
                'Aasta': aasta,
                'Algbilanss': round(algbilanss, 2),
                'Mart_Laen_Algus': round(alglaenud['Mart'], 2),
                'Kerli_Laen_Algus': round(alglaenud['Kerli'], 2),
                'Laps1_Laen_Algus': round(alglaenud['Laps1'], 2),
                'Laps2_Laen_Algus': round(alglaenud['Laps2'], 2),
                'Kogulaaen_Algus': round(kogulaaen_algus, 2),
                'Aastasissemakse': round(aasta_sissemakse, 2),
                'Mart_Lisa': round(laenu_lisad['Mart'], 2),
                'Kerli_Lisa': round(laenu_lisad['Kerli'], 2),
                'Laps1_Lisa': round(laenu_lisad['Laps1'], 2),
                'Laps2_Lisa': round(laenu_lisad['Laps2'], 2),
                'Uuri_Tulu': round(uuri_tulu, 2),
                'Investeerimiskasum': round(investeerimiskasum, 2),
                'Uuri_Tagasimakse': round(uuri_tagasimakse, 2),
                'Mart_Tagasimakse': round(laenu_vahenemised['Mart'], 2),
                'Kerli_Tagasimakse': round(laenu_vahenemised['Kerli'], 2),
                'Loppbilanss': round(loppbilanss, 2),
                'Mart_Laen_Lopp': round(lopp_laenud['Mart'], 2),
                'Kerli_Laen_Lopp': round(lopp_laenud['Kerli'], 2),
                'Laps1_Laen_Lopp': round(lopp_laenud['Laps1'], 2),
                'Laps2_Laen_Lopp': round(lopp_laenud['Laps2'], 2),
                'Kogulaaen_Lopp': round(kogulaaen_lopp, 2),
                'Kasumid': round(kasumid, 2),
                'Uuri_Hypoteek': round(self.arvuta_uuri_hypoteek(aasta), 2)
            }
            
            tulemused.append(tulemus)
            
            # Prepare for next year
            eelmine_bilanss = loppbilanss
            eelmised_laenud = lopp_laenud.copy()
        
        return pd.DataFrame(tulemused)
    
    def arvuta_koik_stsenaariumid(self) -> dict[str, pd.DataFrame]:
        """
        Calculate all 9 scenarios (3 contribution × 3 return).
        
        Returns:
            Dictionary mapping scenario names to DataFrames.
        """
        koik_tulemused: dict[str, pd.DataFrame] = {}
        
        for sisend_sts in InvestmentConstants.VALID_SCENARIOS:
            for tootlus_sts in InvestmentConstants.VALID_SCENARIOS:
                nimi = f"{sisend_sts}_{tootlus_sts}"
                print(f"Arvutan stsenaariumi: {nimi}...")
                df = self.arvuta_stsenaarium(sisend_sts, tootlus_sts)
                koik_tulemused[nimi] = df
        
        print("✅ Kõik stsenaariumid arvutatud!\n")
        return koik_tulemused
    
    def loo_kokkuvote(self, koik_tulemused: dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Create summary table from all scenarios.
        
        Args:
            koik_tulemused: Dictionary of scenario DataFrames.
            
        Returns:
            Summary DataFrame.
        """
        kokkuvote = []
        
        for nimi, df in koik_tulemused.items():
            df_2026 = df[df['Aasta'] == 2026].iloc[0]
            df_2030 = df[df['Aasta'] == 2030].iloc[0]
            df_2031 = df[df['Aasta'] == 2031].iloc[0]
            df_2035 = df[df['Aasta'] == 2035].iloc[0]
            df_2040 = df[df['Aasta'] == 2040].iloc[0]
            
            # Parse scenario for contribution and return rates
            sissemakse_sts, tootlus_sts = nimi.split('_')
            kuumakse = sum(self.config.sissemaksed[sissemakse_sts].values())
            tootlus_prot = self.config.tootlused[tootlus_sts] * 100
            
            kokkuvote.append({
                'Stsenaarium': nimi,
                'Kuumakse': f"€{kuumakse}",
                'Tootlus': f"{tootlus_prot}%",
                '2026_OU': df_2026['Loppbilanss'],
                '2030_OU': df_2030['Loppbilanss'],
                '2030_Laenud': df_2030['Kogulaaen_Lopp'],
                '2030_Kasumid': df_2030['Kasumid'],
                '2030_Uuri_Hypoteek': df_2030['Uuri_Hypoteek'],
                '2031_OU': df_2031['Loppbilanss'],
                '2031_Laenud': df_2031['Kogulaaen_Lopp'],
                '2031_Kasumid': df_2031['Kasumid'],
                '2035_OU': df_2035['Loppbilanss'],
                '2035_Laenud': df_2035['Kogulaaen_Lopp'],
                '2035_Kasumid': df_2035['Kasumid'],
                '2040_OU': df_2040['Loppbilanss'],
                '2040_Laenud': df_2040['Kogulaaen_Lopp'],
                '2040_Kasumid': df_2040['Kasumid'],
            })
        
        return pd.DataFrame(kokkuvote)
    
    def loo_laenude_detailne_kokkuvote(
        self, 
        koik_tulemused: dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Create detailed loan breakdown.
        
        Args:
            koik_tulemused: Dictionary of scenario DataFrames.
            
        Returns:
            Loan detail DataFrame.
        """
        laenu_kokkuvote = []
        
        for nimi, df in koik_tulemused.items():
            df_2030 = df[df['Aasta'] == 2030].iloc[0]
            df_2031 = df[df['Aasta'] == 2031].iloc[0]
            df_2040 = df[df['Aasta'] == 2040].iloc[0]
            
            laenu_kokkuvote.append({
                'Stsenaarium': nimi,
                '2030_Mart': df_2030['Mart_Laen_Lopp'],
                '2030_Kerli': df_2030['Kerli_Laen_Lopp'],
                '2030_Laps1': df_2030['Laps1_Laen_Lopp'],
                '2030_Laps2': df_2030['Laps2_Laen_Lopp'],
                '2031_Mart': df_2031['Mart_Laen_Lopp'],
                '2031_Kerli': df_2031['Kerli_Laen_Lopp'],
                '2031_Laps1': df_2031['Laps1_Laen_Lopp'],
                '2031_Laps2': df_2031['Laps2_Laen_Lopp'],
                '2040_Mart': df_2040['Mart_Laen_Lopp'],
                '2040_Kerli': df_2040['Kerli_Laen_Lopp'],
                '2040_Laps1': df_2040['Laps1_Laen_Lopp'],
                '2040_Laps2': df_2040['Laps2_Laen_Lopp'],
            })
        
        return pd.DataFrame(laenu_kokkuvote)
    
    def salvesta_csv(
        self, 
        koik_tulemused: dict[str, pd.DataFrame], 
        kokkuvote: pd.DataFrame, 
        laenu_kokkuvote: pd.DataFrame, 
        kataloog: str = 'ou_tulemused'
    ) -> None:
        """
        Save all results to CSV files.
        
        Args:
            koik_tulemused: Dictionary of scenario DataFrames.
            kokkuvote: Summary DataFrame.
            laenu_kokkuvote: Loan detail DataFrame.
            kataloog: Output directory path.
        """
        # Use pathlib for safe path handling
        kataloog_path = Path(kataloog)
        kataloog_path.mkdir(parents=True, exist_ok=True)
        
        # Save each scenario
        for nimi, df in koik_tulemused.items():
            # Sanitize filename (nimi is from controlled sources, but good practice)
            safe_name = "".join(c for c in nimi if c.isalnum() or c == '_')
            failinimi = kataloog_path / f"{safe_name}.csv"
            df.to_csv(failinimi, index=False, encoding='utf-8-sig', sep=';', decimal=',')
            print(f"✅ Salvestatud: {failinimi}")
        
        # Save summaries
        kokkuvote_path = kataloog_path / "KOKKUVOTE.csv"
        kokkuvote.to_csv(kokkuvote_path, index=False, encoding='utf-8-sig', sep=';', decimal=',')
        print(f"✅ Salvestatud: {kokkuvote_path}")
        
        laenu_path = kataloog_path / "LAENUDE_KOKKUVOTE.csv"
        laenu_kokkuvote.to_csv(laenu_path, index=False, encoding='utf-8-sig', sep=';', decimal=',')
        print(f"✅ Salvestatud: {laenu_path}")
        
        print(f"\n🎉 Kõik failid salvestatud kataloogi: {kataloog_path}/")
    
    def kuva_kokkuvote(self, kokkuvote: pd.DataFrame) -> None:
        """
        Display formatted summary.
        
        Args:
            kokkuvote: Summary DataFrame.
        """
        print("\n" + "="*120)
        print("OÜ INVESTEERIMISE KOKKUVÕTE - KÕIK STSENAARIUMID (2026-2040)")
        print("="*120 + "\n")
        
        # Format as Euro (except Kuumakse and Tootlus)
        euro_veerud = [
            col for col in kokkuvote.columns 
            if col not in ['Stsenaarium', 'Kuumakse', 'Tootlus']
        ]
        
        df_kuvamiseks = kokkuvote.copy()
        for veerg in euro_veerud:
            df_kuvamiseks[veerg] = df_kuvamiseks[veerg].apply(lambda x: f"€{x:,.0f}")
        
        print(df_kuvamiseks.to_string(index=False))
        print("\n" + "="*120)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='OÜ Investment Model - Estonian company investment simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Run all scenarios
  %(prog)s --scenario KESKMINE      Run all scenarios with KESKMINE contribution
  %(prog)s --scenario KESKMINE_HEA  Run specific scenario
  %(prog)s --output my_results      Custom output directory
  %(prog)s --no-save                Display only, don't save CSV files
        """
    )
    
    parser.add_argument(
        '--scenario', '-s',
        type=str,
        default=None,
        help='Specific scenario to run (e.g., HEA, KESKMINE_HEA). '
             'If single word, runs all return scenarios for that contribution level.'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='ou_tulemused',
        help='Output directory for CSV files (default: ou_tulemused)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Display results but do not save CSV files'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress initial data printout'
    )
    
    return parser


def run_selected_scenarios(
    mudel: OUInvestmentModel, 
    scenario_filter: Optional[str]
) -> dict[str, pd.DataFrame]:
    """
    Run scenarios based on filter.
    
    Args:
        mudel: The investment model instance.
        scenario_filter: Optional filter string.
        
    Returns:
        Dictionary of scenario results.
    """
    if scenario_filter is None:
        # Run all scenarios
        return mudel.arvuta_koik_stsenaariumid()
    
    # Check if it's a specific scenario (contains underscore)
    if '_' in scenario_filter:
        parts = scenario_filter.upper().split('_')
        if len(parts) == 2:
            sissemakse, tootlus = parts
            print(f"Arvutan stsenaariumi: {scenario_filter.upper()}...")
            df = mudel.arvuta_stsenaarium(sissemakse, tootlus)
            return {scenario_filter.upper(): df}
    
    # It's a contribution level - run all return scenarios for it
    sissemakse = scenario_filter.upper()
    mudel._validate_scenario(sissemakse, "contribution")
    
    tulemused: dict[str, pd.DataFrame] = {}
    for tootlus in InvestmentConstants.VALID_SCENARIOS:
        nimi = f"{sissemakse}_{tootlus}"
        print(f"Arvutan stsenaariumi: {nimi}...")
        df = mudel.arvuta_stsenaarium(sissemakse, tootlus)
        tulemused[nimi] = df
    
    print("✅ Valitud stsenaariumid arvutatud!\n")
    return tulemused


def main() -> None:
    """Main function with CLI argument support."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    print("\n" + "🚀 "*20)
    print("OÜ INVESTEERIMISMUDELI TÄIELIK ARVUTUS")
    print("🚀 "*20)
    
    # Create model (suppress output if quiet mode)
    if args.quiet:
        # Temporarily suppress output
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        mudel = OUInvestmentModel()
        sys.stdout = old_stdout
    else:
        mudel = OUInvestmentModel()
    
    # Calculate scenarios
    print("\n📊 Arvutan stsenaariume...\n")
    koik_tulemused = run_selected_scenarios(mudel, args.scenario)
    
    # Create summaries
    print("📋 Loon kokkuvõtteid...")
    kokkuvote = mudel.loo_kokkuvote(koik_tulemused)
    laenu_kokkuvote = mudel.loo_laenude_detailne_kokkuvote(koik_tulemused)
    
    # Display summary
    mudel.kuva_kokkuvote(kokkuvote)
    
    # Save to CSV (unless --no-save)
    if not args.no_save:
        print("\n💾 Salvestan tulemusi CSV failideks...\n")
        mudel.salvesta_csv(koik_tulemused, kokkuvote, laenu_kokkuvote, args.output)
    else:
        print("\n⏭️  CSV salvestamine vahele jäetud (--no-save)")
    
    # Show example for first scenario
    first_scenario = next(iter(koik_tulemused.keys()))
    print("\n" + "="*120)
    print(f"NÄIDE: {first_scenario} stsenaarium (2026-2035):")
    print("="*120)
    
    df_naide = koik_tulemused[first_scenario][
        ['Aasta', 'Loppbilanss', 'Kogulaaen_Lopp', 'Kasumid', 'Uuri_Hypoteek']
    ]
    df_naide_vorm = df_naide[df_naide['Aasta'] <= 2035].copy()
    
    for col in ['Loppbilanss', 'Kogulaaen_Lopp', 'Kasumid', 'Uuri_Hypoteek']:
        df_naide_vorm[col] = df_naide_vorm[col].apply(lambda x: f"€{x:,.0f}")
    
    print(df_naide_vorm.to_string(index=False))
    print("="*120)
    
    print("\n✅ VALMIS!")
    if not args.no_save:
        print(f"\n📂 Kõik CSV failid on kataloogi '{args.output}/' salvestatud.")
        print("📊 Saad avada faile Excelis või Google Sheetsis (kasuta CSV importi, eraldaja ';')")
    print("\n" + "🎉 "*20 + "\n")


if __name__ == "__main__":
    main()