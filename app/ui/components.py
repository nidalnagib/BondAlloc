import streamlit as st
import pandas as pd
from typing import List, Optional
from app.data.models import Bond, PortfolioConstraints, CreditRating, OptimizationResult, RatingGrade
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
                value=1.0,
                step=0.1,
                format="%.1f"
            ) / 100.0
        with col2:
            max_position_size = st.number_input(
                "Maximum Position Size (%)",
                min_value=min_position_size * 100,
                max_value=100.0,
                value=max(20.0, min_position_size * 100),
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

        # Grade constraints
        st.subheader("High Yield Exposure Constraints")
        st.info("Set minimum and maximum exposure to High Yield bonds")
        
        grade_constraints = {}
        col1, col2 = st.columns(2)
        with col1:
            min_hy = st.number_input(
                "Min High Yield (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
                format="%.1f",
                key="min_high_yield"
            ) / 100.0
        with col2:
            max_hy = st.number_input(
                "Max High Yield (%)",
                min_value=float(min_hy * 100),
                max_value=100.0,
                value=40.0,
                step=1.0,
                format="%.1f",
                key="max_high_yield"
            ) / 100.0
        
        if min_hy > 0 or max_hy < 1:
            grade_constraints[RatingGrade.HIGH_YIELD] = (min_hy, max_hy)

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
                    max_issuer_exposure=max_issuer_exposure,
                    grade_constraints=grade_constraints
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

    # Grade exposures
    st.subheader("Rating Grade Exposures")
    grade_cols = st.columns(len(RatingGrade))
    for i, grade in enumerate(RatingGrade):
        with grade_cols[i]:
            exposure = result.metrics.get(f'grade_{grade.value}', 0)
            st.metric(grade.value, f"{exposure:.1%}")

    # Portfolio breakdown
    st.subheader("Portfolio Breakdown")
    col1, col2 = st.columns(2)
    
    # Create portfolio dataframe
    portfolio_data = []
    total_size = result.metrics.get('total_size', 10_000_000)  # Default to 10M if not provided
    
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
            'isin': isin,
            'weight': weight,
            'country': bond.country,
            'rating': bond.credit_rating.display(),
            'issuer': bond.issuer,
            'coupon': bond.coupon_rate,
            'maturity': bond.maturity_date,
            'ytm': bond.ytm,
            'duration': bond.modified_duration,
            'grade': bond.rating_grade.value,
            'target_notional': notional,
            'rounded_notional': rounded_notional,
            'min_piece': min_notional,
            'increment': increment,
            'warning': warning
        })
    df_portfolio = pd.DataFrame(portfolio_data)
    
    # Add rounded weight column
    df_portfolio['rounded_weight'] = df_portfolio['rounded_notional'] / total_size
    
    # Country breakdown pie chart
    with col1:
        country_weights = df_portfolio.groupby('country')['weight'].sum()
        fig = px.pie(
            values=country_weights.values,
            names=country_weights.index,
            title='Country Breakdown'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Rating breakdown
    with col2:
        # Create two bar charts
        fig = go.Figure()
        
        # Detailed rating breakdown
        rating_weights = df_portfolio.groupby('rating')['weight'].sum()
        fig.add_trace(go.Bar(
            x=rating_weights.index,
            y=rating_weights.values * 100,
            name='By Rating',
            visible=True
        ))
        
        # IG/HY breakdown
        grade_weights = df_portfolio.groupby('grade')['weight'].sum()
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

    # Cash flow distribution
    st.subheader("Cash Flow Distribution")
    years = range(datetime.now().year, max(df_portfolio['maturity']).year + 1)
    coupons = []
    redemptions = []
    
    for year in years:
        # Calculate coupon payments using rounded notionals
        year_coupons = sum(
            row['rounded_notional'] * row['coupon']
            for _, row in df_portfolio.iterrows()
            if row['maturity'].year >= year
        )
        coupons.append(year_coupons)
        
        # Calculate redemptions using rounded notionals
        year_redemptions = sum(
            row['rounded_notional']
            for _, row in df_portfolio.iterrows()
            if row['maturity'].year == year
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

    col1, col2 = st.columns(2)

    with col1:
        # Top 10 issuers
        st.subheader("Top 10 Issuers")
        issuer_weights = df_portfolio.groupby('issuer')['weight'].sum().sort_values(ascending=False).head(10)
        issuer_df = pd.DataFrame({
            'Issuer': issuer_weights.index,
            'Weight': issuer_weights.values * 100  # Convert to percentage
        })
        st.dataframe(
            issuer_df,
            column_config={
                'Weight': st.column_config.NumberColumn(
                    'Weight',
                    format="%.1f%%"  # Use % format with one decimal place
                )
            },
            hide_index=True
        )
    
    with col2:
        # Top 10 bonds
        st.subheader("Top 10 Bonds")
        top_bonds = df_portfolio.nlargest(10, 'weight')[
            ['isin', 'issuer', 'coupon', 'maturity', 'ytm', 'weight']
        ].copy()
        top_bonds['coupon'] = top_bonds['coupon'].map('{:.2%}'.format)
        top_bonds['ytm'] = top_bonds['ytm'].map('{:.2%}'.format)
        top_bonds['weight'] = top_bonds['weight'].map('{:.2%}'.format)
        top_bonds['maturity'] = top_bonds['maturity'].dt.strftime('%Y-%m-%d')
    
        st.dataframe(top_bonds, hide_index=True)

    # Complete portfolio
    st.subheader("Complete Portfolio")
    df_display = df_portfolio.copy()
    df_display['ytm'] = df_display['ytm'].map('{:.2%}'.format)
    df_display['weight'] = df_display['weight'].map('{:.2%}'.format)
    df_display['rounded_weight'] = df_display['rounded_weight'].map('{:.2%}'.format)
    df_display['coupon'] = df_display['coupon'].map('{:.2%}'.format)
    df_display['maturity'] = df_display['maturity'].dt.strftime('%Y-%m-%d')
    df_display['target_notional'] = df_display['target_notional'].map('{:,.0f}'.format)
    df_display['rounded_notional'] = df_display['rounded_notional'].map('{:,.0f}'.format)
    df_display['min_piece'] = df_display['min_piece'].map('{:,.0f}'.format)
    df_display['increment'] = df_display['increment'].map('{:,.0f}'.format)
    
    st.dataframe(
        df_display,
        column_config={
            'isin': 'ISIN',
            'issuer': 'Issuer',
            'rating': 'Rating',
            'ytm': 'YTM',
            'duration': 'Duration',
            'weight': 'Target Weight',
            'rounded_weight': 'Rounded Weight',
            'target_notional': 'Target Notional',
            'rounded_notional': 'Rounded Notional',
            'min_piece': 'Min Piece',
            'increment': 'Increment',
            'country': 'Country',
            'coupon': 'Coupon',
            'maturity': 'Maturity',
            'grade': 'Grade',
            'warning': 'Warning'
        },
        hide_index=True
    )
    
    # Add CSV download button
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Portfolio as CSV",
        csv,
        "portfolio.csv",
        "text/csv",
        key='download-csv'
    )

    # Display any warnings about position sizes
    warnings = df_portfolio[df_portfolio['warning'] != '']
    if not warnings.empty:
        st.warning("Position Size Adjustments Required:")
        for _, row in warnings.iterrows():
            st.write(f"- {row['isin']} ({row['issuer']}): {row['warning']}")

    # Show total portfolio metrics after rounding
    if len(df_portfolio) > 0:
        st.subheader("Portfolio Summary")
        total_target = df_portfolio['target_notional'].sum()
        total_rounded = df_portfolio['rounded_notional'].sum()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Target Size", f"{total_target:,.0f}")
        with col2:
            st.metric("Total Rounded Size", f"{total_rounded:,.0f}")
        with col3:
            diff_pct = (total_rounded - total_target) / total_target * 100
            st.metric("Size Difference", f"{diff_pct:+.2f}%")
