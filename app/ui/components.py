import streamlit as st
import pandas as pd
from typing import List, Optional
from app.data.models import Bond, PortfolioConstraints, CreditRating, OptimizationResult
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np


def render_constraints_form() -> Optional[PortfolioConstraints]:
    """Render form for portfolio constraints"""
    with st.form("constraints_form"):
        st.subheader("Portfolio Constraints")

        # Total size
        total_size = st.number_input(
            "Total Portfolio Size",
            min_value=1_000_000,
            max_value=1_000_000_000,
            value=10_000_000,
            step=1_000_000,
            format="%d"
        )

        # Securities count
        col1, col2 = st.columns(2)
        with col1:
            min_securities = st.number_input(
                "Minimum Securities",
                min_value=1,
                max_value=50,
                value=5,
                step=1
            )
        with col2:
            max_securities = st.number_input(
                "Maximum Securities",
                min_value=min_securities,
                max_value=50,
                value=max(15, min_securities),
                step=1
            )

        # Duration
        col1, col2 = st.columns(2)
        with col1:
            target_duration = st.number_input(
                "Target Duration",
                min_value=0.0,
                max_value=30.0,
                value=5.0,
                step=0.1,
                format="%.2f"
            )
        with col2:
            duration_tolerance = st.number_input(
                "Duration Tolerance",
                min_value=0.0,
                max_value=5.0,
                value=0.9,
                step=0.1,
                format="%.2f"
            )

        # Rating
        col1, col2 = st.columns(2)
        with col1:
            # Create rating options with display values
            rating_options = {r: r.display() for r in CreditRating}
            rating_display_to_enum = {v: k for k, v in rating_options.items()}

            min_rating_display = st.selectbox(
                "Minimum Rating",
                options=list(rating_display_to_enum.keys()),
                index=list(rating_display_to_enum.keys()).index('AA')  # Default to AA
            )
            min_rating = rating_display_to_enum[min_rating_display]

        with col2:
            rating_tolerance = st.number_input(
                "Rating Tolerance (notches)",
                min_value=0,
                max_value=5,
                value=1,
                step=1
            )

        # Yield
        col1, _ = st.columns([1, 1])
        with col1:
            min_yield = st.number_input(
                "Minimum Yield (%)",
                min_value=0.0,
                max_value=100.0,
                value=2.0,
                step=0.1,
                format="%.1f"
            ) / 100.0

        # Position size
        col1, col2 = st.columns(2)
        with col1:
            min_position_size = st.number_input(
                "Minimum Position Size (%)",
                min_value=0.0,
                max_value=100.0,
                value=2.0,
                step=0.1,
                format="%.1f"
            ) / 100.0
        with col2:
            max_position_size = st.number_input(
                "Maximum Position Size (%)",
                min_value=min_position_size * 100,
                max_value=100.0,
                value=max(10.0, min_position_size * 100),
                step=0.1,
                format="%.1f"
            ) / 100.0

        # Issuer exposure
        col1, _ = st.columns([1, 1])
        with col1:
            max_issuer_exposure = st.number_input(
                "Maximum Issuer Exposure (%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                step=0.1,
                format="%.1f"
            ) / 100.0

        submitted = st.form_submit_button("Run Optimization")

        if submitted:
            try:
                return PortfolioConstraints(
                    total_size=total_size,
                    min_securities=min_securities,
                    max_securities=max_securities,
                    target_duration=target_duration,
                    duration_tolerance=duration_tolerance,
                    min_rating=min_rating,
                    rating_tolerance=rating_tolerance,
                    min_yield=min_yield,
                    min_position_size=min_position_size,
                    max_position_size=max_position_size,
                    max_issuer_exposure=max_issuer_exposure
                )
            except ValidationError as e:
                st.error(f"Invalid constraints: {str(e)}")
                return None

    return None


def display_optimization_results(result: OptimizationResult, universe: List[Bond], total_size: float):
    """Display optimization results in a formatted way"""
    if not result.success:
        st.error("Optimization failed to find a solution")
        if result.constraint_violations:
            st.write("Constraint violations:")
            for violation in result.constraint_violations:
                st.write(f"- {violation}")
        return

    if not result.constraints_satisfied:
        st.warning("Found a solution but some constraints are slightly violated")
        if result.constraint_violations:
            st.write("Constraint violations (may be due to numerical precision):")
            for violation in result.constraint_violations:
                st.write(f"- {violation}")

    # Portfolio metrics
    st.subheader("Portfolio Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Yield", f"{result.metrics['yield']:.2%}")
    with col2:
        st.metric("Duration", f"{result.metrics['duration']:.4f}")
    with col3:
        rating_score = result.metrics['rating']
        rating = CreditRating.from_score(float(rating_score))
        st.metric(
            "Rating",
            rating.display(),
            help="Portfolio average rating calculated on a logarithmic scale where AAA=1, AA+=2, AA=3, etc. Lower score means better rating."
        )
    with col4:
        st.metric("Number of Securities", f"{int(result.metrics['number_of_securities'])}")

    # Create portfolio data
    portfolio_data = []
    for isin, weight in result.portfolio.items():
        bond = next(b for b in universe if b.isin == isin)
        notional = weight * total_size
        min_notional = bond.min_piece
        increment = bond.increment_size

        # Calculate rounded notional
        if notional < min_notional:
            warning = f"Position too small (min: {min_notional:,.0f})"
            rounded_notional = 0
        else:
            rounded_notional = (notional // increment) * increment
            if rounded_notional < min_notional:
                rounded_notional = min_notional
                warning = f"Rounded up to minimum piece size ({min_notional:,.0f})"
            else:
                warning = ""

        portfolio_data.append({
            'ISIN': isin,
            'Issuer': bond.issuer,
            'Rating': bond.credit_rating.display(),
            'YTM': bond.ytm,
            'Duration': bond.modified_duration,
            'Weight': weight,
            'Target Notional': notional,
            'Rounded Notional': rounded_notional,
            'Min Piece': min_notional,
            'Increment': increment,
            'Warning': warning,
            'Country': getattr(bond, 'country', 'Unknown'),
            'Coupon': bond.coupon_rate,
            'Maturity': bond.maturity_date
        })

    df = pd.DataFrame(portfolio_data)
    
    # Display visualizations in tabs
    tab1, tab2, tab3 = st.tabs(["Portfolio Breakdown", "Cash Flows", "Top Holdings"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        # Country breakdown pie chart
        with col1:
            country_weights = df.groupby('Country')['Weight'].sum()
            fig = px.pie(
                values=country_weights.values,
                names=country_weights.index,
                title='Country Breakdown'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Rating breakdown
        with col2:
            # Add investment grade flag
            df['Grade'] = df['Rating'].apply(lambda x: 'Investment Grade' if x in ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-'] else 'High Yield')
            
            # Create two bar charts
            fig = go.Figure()
            
            # Detailed rating breakdown
            rating_weights = df.groupby('Rating')['Weight'].sum()
            fig.add_trace(go.Bar(
                x=rating_weights.index,
                y=rating_weights.values * 100,
                name='By Rating',
                visible=True
            ))
            
            # IG/HY breakdown
            grade_weights = df.groupby('Grade')['Weight'].sum()
            fig.add_trace(go.Bar(
                x=grade_weights.index,
                y=grade_weights.values * 100,
                name='By Grade',
                visible=False
            ))
            
            # Add buttons to switch between views
            fig.update_layout(
                title='Rating Breakdown',
                yaxis_title='Weight (%)',
                updatemenus=[{
                    'buttons': [
                        {'label': 'By Rating', 'method': 'update', 'args': [{'visible': [True, False]}]},
                        {'label': 'By Grade', 'method': 'update', 'args': [{'visible': [False, True]}]}
                    ],
                    'direction': 'down',
                    'showactive': True,
                }]
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Cash flow distribution
        years = range(datetime.now().year, max(df['Maturity']).year + 1)
        coupons = []
        redemptions = []
        
        for year in years:
            # Calculate coupon payments
            year_coupons = sum(
                row['Rounded Notional'] * row['Coupon']
                for _, row in df.iterrows()
                if row['Maturity'].year >= year
            )
            coupons.append(year_coupons)
            
            # Calculate redemptions
            year_redemptions = sum(
                row['Rounded Notional']
                for _, row in df.iterrows()
                if row['Maturity'].year == year
            )
            redemptions.append(year_redemptions)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(years),
            y=coupons,
            name='Coupons'
        ))
        fig.add_trace(go.Bar(
            x=list(years),
            y=redemptions,
            name='Redemptions'
        ))
        
        fig.update_layout(
            title='Cash Flow Distribution',
            xaxis_title='Year',
            yaxis_title='Amount',
            barmode='stack'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Top 10 issuers
        st.subheader("Top 10 Issuers")
        issuer_weights = df.groupby('Issuer')['Weight'].sum().sort_values(ascending=False).head(10)
        issuer_df = pd.DataFrame({
            'Issuer': issuer_weights.index,
            'Weight': issuer_weights.values
        })
        st.dataframe(
            issuer_df,
            column_config={
                'Weight': st.column_config.NumberColumn(
                    'Weight',
                    format="%.2%"
                )
            },
            hide_index=True
        )
        
        # Top 10 bonds
        st.subheader("Top 10 Bonds")
        top_bonds = df.nlargest(10, 'Weight')[
            ['ISIN', 'Issuer', 'Coupon', 'Maturity', 'YTM', 'Weight']
        ].copy()
        top_bonds['Coupon'] = top_bonds['Coupon'].map('{:.2%}'.format)
        top_bonds['YTM'] = top_bonds['YTM'].map('{:.2%}'.format)
        top_bonds['Weight'] = top_bonds['Weight'].map('{:.2%}'.format)
        top_bonds['Maturity'] = top_bonds['Maturity'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(top_bonds, hide_index=True)

    # Original portfolio composition table
    st.subheader("Complete Portfolio")
    df_display = df.copy()
    df_display['YTM'] = df_display['YTM'].map('{:.2%}'.format)
    df_display['Weight'] = df_display['Weight'].map('{:.2%}'.format)
    df_display['Target Notional'] = df_display['Target Notional'].map('{:,.0f}'.format)
    df_display['Rounded Notional'] = df_display['Rounded Notional'].map('{:,.0f}'.format)
    df_display['Min Piece'] = df_display['Min Piece'].map('{:,.0f}'.format)
    df_display['Increment'] = df_display['Increment'].map('{:,.0f}'.format)
    
    st.dataframe(
        df_display,
        column_config={
            'ISIN': 'ISIN',
            'Issuer': 'Issuer',
            'Rating': 'Rating',
            'YTM': 'YTM',
            'Duration': 'Duration',
            'Weight': 'Weight',
            'Target Notional': 'Target Notional',
            'Rounded Notional': 'Rounded Notional',
            'Min Piece': 'Min Piece',
            'Increment': 'Increment',
            'Warning': 'Warning'
        },
        hide_index=True
    )

    # Display any warnings about position sizes
    warnings = df[df['Warning'] != '']
    if not warnings.empty:
        st.warning("Position Size Adjustments Required:")
        for _, row in warnings.iterrows():
            st.write(f"- {row['ISIN']} ({row['Issuer']}): {row['Warning']}")

    # Show total portfolio metrics after rounding
    if len(df) > 0:
        st.subheader("Portfolio Summary After Rounding")
        total_target = df['Target Notional'].astype(float).sum()
        total_rounded = df['Rounded Notional'].astype(float).sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Target Size", f"{total_target:,.0f}")
        with col2:
            st.metric("Total Rounded Size", f"{total_rounded:,.0f}")
        with col3:
            diff_pct = (total_rounded - total_target) / total_target * 100
            st.metric("Size Difference", f"{diff_pct:+.2f}%")
