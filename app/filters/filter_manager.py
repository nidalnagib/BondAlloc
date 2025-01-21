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
        
        # Start with all bonds included
        mask = pd.Series([True] * len(df))
        
        # Apply exclusion groups if present
        if 'exclusion_groups' in filter_config:
            group_masks = []
            for group in filter_config['exclusion_groups']:
                # Start with all True for this group
                group_mask = pd.Series([True] * len(df))
                # Apply all conditions in the group (AND logic)
                for condition in group['conditions']:
                    field = condition['category']
                    value = condition['value']
                    if field in df.columns:
                        group_mask &= (df[field] == value)
                group_masks.append(group_mask)
            
            # Combine all group masks with OR logic and invert (we want to exclude matches)
            if group_masks:
                exclude_mask = pd.concat(group_masks, axis=1).any(axis=1)
                mask &= ~exclude_mask
        
        # Apply range filters if present
        if 'range_filters' in filter_config:
            for field, range_spec in filter_config['range_filters'].items():
                if field in df.columns:
                    if 'min' in range_spec:
                        mask &= df[field] >= range_spec['min']
                    if 'max' in range_spec:
                        mask &= df[field] <= range_spec['max']
        
        # Convert back to list of Bond objects
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
    
    def save_predefined_filter(self, name: str, description: str, filter_config: Dict[str, Any]) -> bool:
        """Save a new predefined filter"""
        if not name or not description:
            return False
            
        # Format the filter entry
        filter_entry = {
            "description": description,
            "filters": filter_config
        }
        
        # Load existing filters
        try:
            with open(self.filters_file, 'r') as f:
                filters = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            filters = {}
            
        # Add new filter
        filters[name] = filter_entry
        
        # Save back to file
        try:
            with open(self.filters_file, 'w') as f:
                json.dump(filters, f, indent=4)
            return True
        except Exception:
            return False
    
    def delete_predefined_filter(self, filter_name: str) -> bool:
        """Delete a predefined filter"""
        try:
            with open(self.filters_file, 'r') as f:
                filters = json.load(f)
                
            if filter_name in filters:
                del filters[filter_name]
                
                with open(self.filters_file, 'w') as f:
                    json.dump(filters, f, indent=4)
                return True
            return False
        except Exception:
            return False
