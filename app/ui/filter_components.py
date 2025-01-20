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
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    if 'filter_to_delete' not in st.session_state:
        st.session_state.filter_to_delete = None
        
    # Initialize filter states from active_filters if they don't exist
    if 'excluded_ratings' not in st.session_state:
        st.session_state.excluded_ratings = st.session_state.active_filters.get('rating', {}).get('values', []) if st.session_state.active_filters and st.session_state.active_filters.get('rating', {}).get('type') == 'categorical_exclude' else []
    if 'excluded_issuers' not in st.session_state:
        st.session_state.excluded_issuers = st.session_state.active_filters.get('issuer', {}).get('values', []) if st.session_state.active_filters and st.session_state.active_filters.get('issuer', {}).get('type') == 'categorical_exclude' else []
    if 'excluded_countries' not in st.session_state:
        st.session_state.excluded_countries = st.session_state.active_filters.get('country', {}).get('values', []) if st.session_state.active_filters and st.session_state.active_filters.get('country', {}).get('type') == 'categorical_exclude' else []
    if 'excluded_sectors' not in st.session_state:
        st.session_state.excluded_sectors = st.session_state.active_filters.get('sector', {}).get('values', []) if st.session_state.active_filters and st.session_state.active_filters.get('sector', {}).get('type') == 'categorical_exclude' else []
    if 'excluded_ranks' not in st.session_state:
        st.session_state.excluded_ranks = st.session_state.active_filters.get('payment_rank', {}).get('values', []) if st.session_state.active_filters and st.session_state.active_filters.get('payment_rank', {}).get('type') == 'categorical_exclude' else []
    if 'ytm_filter_min' not in st.session_state:
        st.session_state.ytm_filter_min = min(bond.ytm for bond in universe)
    if 'ytm_filter_max' not in st.session_state:
        st.session_state.ytm_filter_max = max(bond.ytm for bond in universe)
    if 'dur_filter_min' not in st.session_state:
        st.session_state.dur_filter_min = min(bond.modified_duration for bond in universe)
    if 'dur_filter_max' not in st.session_state:
        st.session_state.dur_filter_max = max(bond.modified_duration for bond in universe)
    
    # Callback functions to update session state
    def on_rating_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_issuer_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_country_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_sector_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_rank_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_ytm_change():
        st.session_state.active_filters = build_filter_config()
        
    def on_dur_change():
        st.session_state.active_filters = build_filter_config()
    
    def build_filter_config():
        config = {}
        if st.session_state.excluded_ratings:
            config['rating'] = {
                'type': 'categorical_exclude',
                'values': st.session_state.excluded_ratings
            }
        if st.session_state.excluded_issuers:
            config['issuer'] = {
                'type': 'categorical_exclude',
                'values': st.session_state.excluded_issuers
            }
        if st.session_state.excluded_countries:
            config['country'] = {
                'type': 'categorical_exclude',
                'values': st.session_state.excluded_countries
            }
        if st.session_state.excluded_sectors:
            config['sector'] = {
                'type': 'categorical_exclude',
                'values': st.session_state.excluded_sectors
            }
        if st.session_state.excluded_ranks:
            config['payment_rank'] = {
                'type': 'categorical_exclude',
                'values': st.session_state.excluded_ranks
            }
        config['ytm'] = {
            'type': 'range',
            'min': st.session_state.ytm_filter_min,
            'max': st.session_state.ytm_filter_max
        }
        config['modified_duration'] = {
            'type': 'range',
            'min': st.session_state.dur_filter_min,
            'max': st.session_state.dur_filter_max
        }
        return config
    
    # Predefined filters
    predefined_filters = filter_manager.get_predefined_filters()
    if predefined_filters:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_filter = st.selectbox(
                "Select a predefined filter",
                options=["None"] + list(predefined_filters.keys()),
                format_func=lambda x: "None" if x == "None" else f"{x} - {predefined_filters[x]}"
            )
        
        with col2:
            if selected_filter != "None":
                # Add empty space to push button to bottom
                st.write("")
                st.write("")
                if st.button("🗑️ Delete Filter"):
                    st.session_state.show_delete_confirmation = True
                    st.session_state.filter_to_delete = selected_filter
        
        # Delete confirmation popup
        if st.session_state.show_delete_confirmation:
            confirm_col1, confirm_col2 = st.columns([1, 1])
            st.warning(f"Are you sure you want to delete the filter '{st.session_state.filter_to_delete}'?")
            
            with confirm_col1:
                if st.button("Yes, Delete"):
                    success = filter_manager.delete_predefined_filter(st.session_state.filter_to_delete)
                    if success:
                        st.success(f"Filter '{st.session_state.filter_to_delete}' deleted successfully!")
                        st.session_state.selected_predefined_filter = "None"
                        st.session_state.active_filters = {}
                    else:
                        st.error("Failed to delete filter. Please try again.")
                    st.session_state.show_delete_confirmation = False
                    st.session_state.filter_to_delete = None
                    st.rerun()
            
            with confirm_col2:
                if st.button("No, Cancel"):
                    st.session_state.show_delete_confirmation = False
                    st.session_state.filter_to_delete = None
        
        # Update session state and get filter details if changed
        if selected_filter != st.session_state.selected_predefined_filter:
            st.session_state.selected_predefined_filter = selected_filter
            if selected_filter != "None":
                filter_config = filter_manager._predefined_filters[selected_filter]['filters']
                st.session_state.active_filters = filter_config
                
                # Update individual filter states
                st.session_state.excluded_ratings = filter_config.get('rating', {}).get('values', []) if filter_config.get('rating', {}).get('type') == 'categorical_exclude' else []
                st.session_state.excluded_issuers = filter_config.get('issuer', {}).get('values', []) if filter_config.get('issuer', {}).get('type') == 'categorical_exclude' else []
                st.session_state.excluded_countries = filter_config.get('country', {}).get('values', []) if filter_config.get('country', {}).get('type') == 'categorical_exclude' else []
                st.session_state.excluded_sectors = filter_config.get('sector', {}).get('values', []) if filter_config.get('sector', {}).get('type') == 'categorical_exclude' else []
                st.session_state.excluded_ranks = filter_config.get('payment_rank', {}).get('values', []) if filter_config.get('payment_rank', {}).get('type') == 'categorical_exclude' else []
                
                # Update range filter states
                if 'ytm' in filter_config:
                    st.session_state.ytm_filter_min = filter_config['ytm'].get('min', min(bond.ytm for bond in universe))
                    st.session_state.ytm_filter_max = filter_config['ytm'].get('max', max(bond.ytm for bond in universe))
                if 'modified_duration' in filter_config:
                    st.session_state.dur_filter_min = filter_config['modified_duration'].get('min', min(bond.modified_duration for bond in universe))
                    st.session_state.dur_filter_max = filter_config['modified_duration'].get('max', max(bond.modified_duration for bond in universe))
            else:
                # Clear all filters when "None" is selected
                st.session_state.active_filters = {}
                st.session_state.excluded_ratings = []
                st.session_state.excluded_issuers = []
                st.session_state.excluded_countries = []
                st.session_state.excluded_sectors = []
                st.session_state.excluded_ranks = []
                st.session_state.ytm_filter_min = min(bond.ytm for bond in universe)
                st.session_state.ytm_filter_max = max(bond.ytm for bond in universe)
                st.session_state.dur_filter_min = min(bond.modified_duration for bond in universe)
                st.session_state.dur_filter_max = max(bond.modified_duration for bond in universe)
    
    # Custom filters
    with st.expander("Custom Filters", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Rating filter
            ratings = sorted(list(set(bond.credit_rating.display() for bond in universe)))
            st.write("Ratings Filter")
            st.multiselect(
                "Exclude Ratings",
                options=ratings,
                key="excluded_ratings",
                on_change=on_rating_change
            )
            
            # Issuer filter
            issuers = sorted(list(set(bond.issuer for bond in universe)))
            st.write("Issuers Filter")
            st.multiselect(
                "Exclude Issuers",
                options=issuers,
                key="excluded_issuers",
                on_change=on_issuer_change
            )
            
            # Country filter
            countries = sorted(list(set(getattr(bond, 'country', 'Unknown') for bond in universe)))
            st.write("Countries Filter")
            st.multiselect(
                "Exclude Countries",
                options=countries,
                key="excluded_countries",
                on_change=on_country_change
            )
        
        with col2:
            # Sector filter
            sectors = sorted(list(set(getattr(bond, 'sector', 'Unknown') for bond in universe)))
            st.write("Sectors Filter")
            st.multiselect(
                "Exclude Sectors",
                options=sectors,
                key="excluded_sectors",
                on_change=on_sector_change
            )
            
            # Payment Rank filter
            ranks = sorted(list(set(getattr(bond, 'payment_rank', 'Unknown') for bond in universe)))
            st.write("Payment Ranks Filter")
            st.multiselect(
                "Exclude Payment Ranks",
                options=ranks,
                key="excluded_ranks",
                on_change=on_rank_change
            )
        
        # YTM range
        ytm_min = min(bond.ytm for bond in universe)
        ytm_max = max(bond.ytm for bond in universe)
        current_ytm = st.session_state.active_filters.get('ytm', {})
        ytm_range = st.slider(
            "YTM Range",
            min_value=float(ytm_min * 100),
            max_value=float(ytm_max * 100),
            value=(
                float(current_ytm.get('min', ytm_min) * 100) if current_ytm else float(ytm_min * 100),
                float(current_ytm.get('max', ytm_max) * 100) if current_ytm else float(ytm_max * 100)
            ),
            format="%.2f%%",
            on_change=on_ytm_change
        )
        
        # Convert YTM back to decimal for filter
        st.session_state.ytm_filter_min = ytm_range[0] / 100
        st.session_state.ytm_filter_max = ytm_range[1] / 100
        
        # Duration range
        dur_min = min(bond.modified_duration for bond in universe)
        dur_max = max(bond.modified_duration for bond in universe)
        current_dur = st.session_state.active_filters.get('modified_duration', {}) or st.session_state.active_filters.get('duration', {})
        dur_range = st.slider(
            "Duration Range",
            min_value=float(dur_min),
            max_value=float(dur_max),
            value=(
                float(current_dur.get('min', dur_min)) if current_dur else float(dur_min),
                float(current_dur.get('max', dur_max)) if current_dur else float(dur_max)
            ),
            format="%.2f",
            on_change=on_dur_change
        )
        
        # Update session state
        st.session_state.dur_filter_min = dur_range[0]
        st.session_state.dur_filter_max = dur_range[1]
        
        # Save filter section
        st.write("---")
        st.write("Save Current Filter")
        col1, col2 = st.columns(2)
        
        with col1:
            filter_name = st.text_input("Filter Name", 
                                      key="save_filter_name", 
                                      placeholder="e.g., High Grade Tech")
        with col2:
            filter_description = st.text_input("Filter Description", 
                                             key="save_filter_desc", 
                                             placeholder="e.g., High grade technology sector bonds")
        
        if st.button("Save as Predefined Filter"):
            if not filter_name or not filter_description:
                st.error("Please provide both a name and description for the filter")
            else:
                success = filter_manager.save_predefined_filter(filter_name, filter_description, st.session_state.active_filters)
                if success:
                    st.success(f"Filter '{filter_name}' saved successfully!")
                else:
                    st.error("Failed to save filter. Please try again.")
                
                # Refresh to update the predefined filters list
                # st.rerun()
        
        # Apply filters
        filtered_universe = filter_manager.apply_filter(universe, st.session_state.active_filters)
        
        # Show filter stats
        st.info(f"Filtered universe: {len(filtered_universe)} bonds (from {len(universe)} total)")
        
        # Save last used filters
        filter_manager.save_last_used(st.session_state.active_filters)
        
        return filtered_universe
    
    return universe
