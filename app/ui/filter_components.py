"""Filter UI components"""
import streamlit as st
from typing import List, Dict, Any, Optional
from app.data.models import Bond
from app.filters import FilterManager
import uuid


# TODO :
#  FIX : When loading filter, category field and value stay sector / airline / defaulted
#  IMPROVE : save filter & delete filter functionnality

def render_filter_controls(universe: List[Bond], filter_manager: FilterManager) -> Optional[List[Bond]]:
    """Render filter controls and return filtered universe"""
    if not universe:
        return None
        
    st.subheader("Universe Filters")
    
    # Initialize session state for filters if not exists
    if 'active_filters' not in st.session_state:
        st.session_state.active_filters = {
            'exclusion_groups': [],
            'range_filters': {
                'ytm': {'min': min(bond.ytm for bond in universe), 'max': max(bond.ytm for bond in universe)},
                'modified_duration': {'min': min(bond.modified_duration for bond in universe), 'max': max(bond.modified_duration for bond in universe)}
            }
        }
    elif not isinstance(st.session_state.active_filters, dict):
        st.session_state.active_filters = {
            'exclusion_groups': [],
            'range_filters': {
                'ytm': {'min': min(bond.ytm for bond in universe), 'max': max(bond.ytm for bond in universe)},
                'modified_duration': {'min': min(bond.modified_duration for bond in universe), 'max': max(bond.modified_duration for bond in universe)}
            }
        }
    else:
        # Ensure all required keys exist
        if 'exclusion_groups' not in st.session_state.active_filters:
            st.session_state.active_filters['exclusion_groups'] = []
        if 'range_filters' not in st.session_state.active_filters:
            st.session_state.active_filters['range_filters'] = {}
        if 'ytm' not in st.session_state.active_filters.get('range_filters', {}):
            st.session_state.active_filters['range_filters']['ytm'] = {
                'min': min(bond.ytm for bond in universe),
                'max': max(bond.ytm for bond in universe)
            }
        if 'modified_duration' not in st.session_state.active_filters.get('range_filters', {}):
            st.session_state.active_filters['range_filters']['modified_duration'] = {
                'min': min(bond.modified_duration for bond in universe),
                'max': max(bond.modified_duration for bond in universe)
            }
    
    if 'selected_predefined_filter' not in st.session_state:
        st.session_state.selected_predefined_filter = "None"
    
    # Predefined filters section
    st.write("Predefined Filters")
    predefined = filter_manager.get_predefined_filters()
    predefined_options = {"None": "No filter"} | predefined
    selected_filter = st.selectbox(
        "Select Filter",
        options=list(predefined_options.keys()),
        format_func=lambda x: f"{x}: {predefined_options[x]}" if x in predefined else x,
        key="selected_predefined_filter"
    )
    
    # Update session state and get filter details if changed
    if selected_filter != "None":
        filter_config = filter_manager._predefined_filters[selected_filter]['filters']
        # Add IDs to groups and conditions if they don't exist
        for group in filter_config['exclusion_groups']:
            if 'id' not in group:
                group['id'] = str(uuid.uuid4())
            for condition in group['conditions']:
                if 'id' not in condition:
                    condition['id'] = str(uuid.uuid4())
        st.session_state.active_filters = filter_config
    
    # Custom filters section
    with st.expander("Custom Filters", expanded=True):
        col1, col2 = st.columns(2)
        
        # Range filters in first column
        with col1:
            st.write("Range Filters")
            
            # YTM filter
            st.write("Yield")
            ytm_min = min(bond.ytm for bond in universe)
            ytm_max = max(bond.ytm for bond in universe)
            current_ytm = st.session_state.active_filters.get('range_filters', {}).get('ytm', {})
            ytm_range = st.slider(
                "",
                min_value=float(ytm_min * 100),
                max_value=float(ytm_max * 100),
                value=(
                    float(current_ytm.get('min', ytm_min) * 100),
                    float(current_ytm.get('max', ytm_max) * 100)
                ),
                step=0.1,
                format="%.1f%%"
            )
            
            # Duration filter
            st.write("Duration")
            dur_min = min(bond.modified_duration for bond in universe)
            dur_max = max(bond.modified_duration for bond in universe)
            current_dur = st.session_state.active_filters.get('range_filters', {}).get('modified_duration', {})
            dur_range = st.slider(
                "",
                min_value=float(dur_min),
                max_value=float(dur_max),
                value=(
                    float(current_dur.get('min', dur_min)),
                    float(current_dur.get('max', dur_max))
                ),
                step=0.1,
                format="%.1f"
            )
            
            # Update range filters in session state
            st.session_state.active_filters['range_filters'] = {
                'ytm': {'min': ytm_range[0] / 100, 'max': ytm_range[1] / 100},
                'modified_duration': {'min': dur_range[0], 'max': dur_range[1]}
            }
        
        # Exclusion groups in second column
        with col2:
            st.write("Exclusion Rules")
            
            # Add new group button
            if st.button("+ Add Exclusion Group"):
                st.session_state.active_filters['exclusion_groups'].append({
                    'id': str(uuid.uuid4()),
                    'conditions': []
                })
            
            # Render each exclusion group
            groups_to_remove = []
            for i, group in enumerate(st.session_state.active_filters['exclusion_groups']):
                with st.container():
                    st.write(f"Group {i + 1}")
                    
                    # Add condition button
                    if st.button(f"+ Add Condition", key=f"add_cond_{group['id']}"):
                        group['conditions'].append({
                            'id': str(uuid.uuid4()),
                            'category': 'sector',
                            'value': None
                        })
                    
                    # Render conditions
                    conditions_to_remove = []
                    for j, condition in enumerate(group['conditions']):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            category = st.selectbox(
                                "Category",
                                options=['sector', 'payment_rank', 'rating', 'issuer', 'country'],
                                key=f"cat_{condition['id']}"
                            )
                            condition['category'] = category
                        
                        with col2:
                            # Get available values for the selected category
                            if category == 'rating':
                                values = sorted(list(set(bond.credit_rating.display() for bond in universe)))
                            else:
                                values = sorted(list(set(getattr(bond, category, 'Unknown') for bond in universe)))
                            
                            value = st.selectbox(
                                "Value",
                                options=values,
                                key=f"val_{condition['id']}"
                            )
                            condition['value'] = value
                        
                        with col3:
                            st.write("")
                            st.write("")
                            if st.button("🗑️", key=f"del_cond_{condition['id']}"):
                                conditions_to_remove.append(j)
                    
                    # Remove marked conditions
                    for j in reversed(conditions_to_remove):
                        group['conditions'].pop(j)
                    
                    # Group delete button
                    if st.button("Delete Group", key=f"del_group_{group['id']}"):
                        groups_to_remove.append(i)
                    
                    st.markdown("---")
            
            # Remove marked groups
            for i in reversed(groups_to_remove):
                st.session_state.active_filters['exclusion_groups'].pop(i)
    
    # Apply filters
    filtered_universe = filter_manager.apply_filter(universe, st.session_state.active_filters)
    
    # Show filter stats
    st.info(f"Remaining {len(filtered_universe)} of {len(universe)} bonds", icon="ℹ️")
    
    return filtered_universe
