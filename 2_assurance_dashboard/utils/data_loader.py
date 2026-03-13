import pandas as pd
import numpy as np
from datetime import datetime

class DataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.raw_df = None

    def load_data(self):
        """Loads and performs basic cleaning."""
        try:
            # Loading with semicolon separator
            self.raw_df = pd.read_csv(self.file_path, sep=';')
            self.df = self.raw_df.copy()
            
            # Convert date column
            self.df['date_derniere_sinistre'] = pd.to_datetime(self.df['date_derniere_sinistre'])
            
            # Perform Feature Engineering
            self._apply_feature_engineering()
            
            return self.df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None

    def _apply_feature_engineering(self):
        """Adds derived variables for analysis."""
        
        # 1. SP Ratio (Loss Ratio)
        # Avoid division by zero
        self.df['ratio_sinistre_prime'] = self.df['montant_sinistres'] / self.df['montant_prime'].replace(0, np.nan)
        
        # 2. Age Segmentation
        bins = [18, 25, 35, 50, 65, 120]
        labels = ['18-25', '26-35', '36-50', '51-65', '65+']
        self.df['segment_age'] = pd.cut(self.df['age'], bins=bins, labels=labels, right=False)
        
        # 3. Recency of last claim (in days)
        today = datetime.now()
        self.df['jours_depuis_sinistre'] = (today - self.df['date_derniere_sinistre']).dt.days
        
        # 4. Risk Score (Simplified formula)
        # Weighting: Nb claims (40%), Total Amount (40%), Bonus/Malus (20%)
        # Normalized between 0 and 100
        
        # Normalization helpers
        def normalize(series):
            return (series - series.min()) / (series.max() - series.min()) if (series.max() - series.min()) != 0 else 0

        norm_nb = normalize(self.df['nb_sinistres'])
        norm_amt = normalize(self.df['montant_sinistres'])
        norm_bm = normalize(self.df['bonus_malus'])
        
        self.df['score_risque'] = (norm_nb * 0.4 + norm_amt * 0.4 + norm_bm * 0.2) * 100
        
        # 5. Profitability (Primes - Claims)
        self.df['rentabilite_nette'] = self.df['montant_prime'] - self.df['montant_sinistres']

    def get_summary_kpis(self):
        """Returns main KPIs for the dashboard."""
        if self.df is None:
            return {}
            
        return {
            'total_primes': self.df['montant_prime'].sum(),
            'total_sinistres': self.df['montant_sinistres'].sum(),
            'loss_ratio_global': (self.df['montant_sinistres'].sum() / self.df['montant_prime'].sum()) * 100,
            'nb_assures': len(self.df),
            'frequence_moyenne': self.df['nb_sinistres'].mean()
        }

if __name__ == "__main__":
    # Test script
    processor = DataProcessor('../data/assurance_data_1000.csv')
    df = processor.load_data()
    if df is not None:
        print("Data loaded successfully!")
        print(df.head())
        print("\nKPIs Summary:")
        print(processor.get_summary_kpis())
