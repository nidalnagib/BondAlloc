"""Filter UI components"""
import streamlit as st
from typing import List, Dict, Any, Optional
from app.data.models import Bond
from app.filters import FilterManager

def render_filter_controls(universe: List[Bond], filter_manager: FilterManager) -> Optional[List[Bond]]:
    """Render filter controls and return filtered universe"""
    if not universe:
        return None
        
    st.subheader("Universe Filters")
    
    # Initialize session state for filters if not exists
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = {}
    if 'selected_predefined_filter' not in st.session_state:
        st.session_state.selected_predefined_filter = "None"
    
    # Predefined filters
    predefined_filters = filter_manager.get_predefined_filters()
    if predefined_filters:
        st.write("Predefined Filters")
        selected_filter = st.selectbox(
            "Select a predefined filter",
            options=["None"] + list(predefined_filters.keys()),
            format_func=lambda x: "None" if x == "None" else f"{x} - {predefined_filters[x]}"
        )
        
        # Update session state and get filter details if changed
        if selected_filter != st.session_state.selected_predefined_filter:
            st.session_state.selected_predefined_filter = selected_filter
            if selected_filter != "None":
                filter_config = filter_manager._predefined_filters[selected_filter]['filters']
                st.session_state.active_filters = filter_config
    
    # Custom filters
    with st.expander("Custom Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        # Get current filter values from session state or defaults
        current_filters = st.session_state.active_filters
        
        with col1:
            # Rating filter
            ratings = sorted(list(set(bond.credit_rating.display() for bond in universe)))
            selected_ratings = st.multiselect(
                "Ratings",
                options=ratings,
                default=current_filters.get('rating', {}).get('values', ratings) if current_filters else ratings
            )
            
            # Country filter
            countries = sorted(list(set(getattr(bond, 'country', 'Unknown') for bond in universe)))
            selected_countries = st.multiselect(
                "Countries",
                options=countries,
                default=current_filters.get('country', {}).get('values', countries) if current_filters else countries
            )
        
        with col2:
            # Sector filter
            sectors = sorted(list(set(getattr(bond, 'sector', 'Unknown') for bond in universe)))
            selected_sectors = st.multiselect(
                "Sectors",
                options=sectors,
                default=current_filters.get('sector', {}).get('values', sectors) if current_filters else sectors
            )
            
            # Payment Rank filter
            ranks = sorted(list(set(getattr(bond, 'payment_rank', 'Unknown') for bond in universe)))
            selected_ranks = st.multiselect(
                "Payment Ranks",
                options=ranks,
                default=current_filters.get('payment_rank', {}).get('values', ranks) if current_filters else ranks
            )
        
        # YTM range
        ytm_min = min(bond.ytm for bond in universe)
        ytm_max = max(bond.ytm for bond in universe)
        current_ytm = current_filters.get('ytm', {})
        ytm_range = st.slider(
            "YTM Range",
            min_value=float(ytm_min * 100),
            max_value=float(ytm_max * 100),
            value=(
                float(current_ytm.get('min', ytm_min) * 100) if current_ytm else float(ytm_min * 100),
                float(current_ytm.get('max', ytm_max) * 100) if current_ytm else float(ytm_max * 100)
            ),
            format="%.2f%%"
        )
        
        # Convert YTM back to decimal for filter
        ytm_filter_min = ytm_range[0] / 100
        ytm_filter_max = ytm_range[1] / 100
        
        # Duration range
        dur_min = min(bond.modified_duration for bond in universe)
        dur_max = max(bond.modified_duration for bond in universe)
        current_dur = current_filters.get('modified_duration', {}) or current_filters.get('duration', {})
        dur_range = st.slider(
            "Duration Range",
            min_value=float(dur_min),
            max_value=float(dur_max),
            value=(
                float(current_dur.get('min', dur_min)) if current_dur else float(dur_min),
                float(current_dur.get('max', dur_max)) if current_dur else float(dur_max)
            ),
            format="%.2f"
        )
        
        # Build filter configuration
        filter_config = {
            'rating': {
                'type': 'categorical',
                'values': selected_ratings
            },
            'country': {
                'type': 'categorical',
                'values': selected_countries
            },
            'sector': {
                'type': 'categorical',
                'values': selected_sectors
            },
            'payment_rank': {
                'type': 'categorical',
                'values': selected_ranks
            },
            'ytm': {
                'type': 'range',
                'min': ytm_filter_min,
                'max': ytm_filter_max
            },
            'modified_duration': {
                'type': 'range',
                'min': dur_range[0],
                'max': dur_range[1]
            }
        }
        
        # Store current filter configuration
        st.session_state.active_filters = filter_config
        
        # Apply filters
        filtered_universe = filter_manager.apply_filter(universe, filter_config)
        
        # Show filter stats
        st.info(f"Filtered universe: {len(filtered_universe)} bonds (from {len(universe)} total)")
        
        # Save last used filters
        filter_manager.save_last_used(filter_config)
        
        return filtered_universe
    
    return universe
