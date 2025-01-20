"""Filter management module"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from app.data.models import Bond

class FilterManager:
    """Manages universe filters"""
    def __init__(self):
        self.filters_path = Path(__file__).parent.parent.parent / "data" / "filters"
        self.filters_file = self.filters_path / "filters.json"
        self.last_used_file = self.filters_path / "last_used.json"
        self._predefined_filters = self._load_predefined_filters()
        
    def _load_predefined_filters(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined filters from JSON file"""
        if not self.filters_file.exists():
            return {}
        with open(self.filters_file, 'r') as f:
            return json.load(f)
    
    def get_predefined_filters(self) -> Dict[str, str]:
        """Get list of predefined filters with descriptions"""
        return {k: v['description'] for k, v in self._predefined_filters.items()}
    
    def apply_filter(self, universe: List[Bond], filter_config: Dict[str, Any]) -> List[Bond]:
        """Apply filter configuration to universe"""
        # Convert bonds to DataFrame for easier filtering
        df = pd.DataFrame([{
            'isin': bond.isin,
            'clean_price': bond.clean_price,
            'ytm': bond.ytm,
            'modified_duration': bond.modified_duration,
            'maturity_date': bond.maturity_date,
            'rating': bond.credit_rating.display(),
            'issuer': bond.issuer,
            'country': getattr(bond, 'country', 'Unknown'),
            'sector': getattr(bond, 'sector', 'Unknown'),
            'payment_rank': getattr(bond, 'payment_rank', 'Unknown')
        } for bond in universe])
        
        mask = pd.Series([True] * len(df))
        
        for field, filter_spec in filter_config.items():
            if filter_spec['type'] == 'categorical':
                if field in df.columns and 'values' in filter_spec:
                    mask &= df[field].isin(filter_spec['values'])
            elif filter_spec['type'] == 'range':
                # Handle both 'duration' and 'modified_duration' fields
                target_field = field
                if field == 'duration':
                    target_field = 'modified_duration'
                
                if target_field in df.columns:
                    if 'min' in filter_spec:
                        mask &= df[target_field] >= filter_spec['min']
                    if 'max' in filter_spec:
                        mask &= df[target_field] <= filter_spec['max']
            elif filter_spec['type'] == 'date_range':
                if field in df.columns:
                    if 'start' in filter_spec:
                        mask &= df[field] >= pd.to_datetime(filter_spec['start'])
                    if 'end' in filter_spec:
                        mask &= df[field] <= pd.to_datetime(filter_spec['end'])
        
        filtered_isins = df[mask]['isin'].tolist()
        return [bond for bond in universe if bond.isin in filtered_isins]
    
    def apply_predefined_filter(self, universe: List[Bond], filter_name: str) -> List[Bond]:
        """Apply a predefined filter to the universe"""
        if filter_name not in self._predefined_filters:
            return universe
        
        filter_config = self._predefined_filters[filter_name]['filters']
        return self.apply_filter(universe, filter_config)
    
    def save_last_used(self, filter_config: Dict[str, Any]) -> None:
        """Save last used filter configuration"""
        with open(self.last_used_file, 'w') as f:
            json.dump(filter_config, f, indent=2)
    
    def load_last_used(self) -> Optional[Dict[str, Any]]:
        """Load last used filter configuration"""
        if not self.last_used_file.exists():
            return None
        try:
            with open(self.last_used_file, 'r') as f:
                return json.load(f)
        except:
            return None
