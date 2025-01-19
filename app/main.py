import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv
import os
import sys
from streamlit.runtime.uploaded_file_manager import UploadedFile
import logging

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.append(str(app_dir))

# Import app modules
from app.data.models import Bond, PortfolioConstraints, CreditRating
from app.optimization.engine import PortfolioOptimizer
from app.ui.components import (
    render_constraints_form,
    display_optimization_results
)

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = Path(app_dir) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"bondalloc_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Load environment variables
load_dotenv()

# Setup logging
loggers = setup_logging()
logger = logging.getLogger('main')

def load_bond_universe(uploaded_file: UploadedFile) -> list[Bond]:
    """Load bond universe from Excel/CSV file"""
    try:
        logger.info(f"Loading bond universe from file: {uploaded_file.name}")
        # Get file extension from the name
        file_extension = Path(uploaded_file.name).suffix.lower()
        
        # Read the file based on its extension
        if file_extension == '.csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file)
        else:
            error_msg = f"Unsupported file format: {file_extension}"
            logger.error(error_msg)
            st.error(error_msg)
            return []
        
        logger.info(f"Successfully loaded {len(df)} rows from file")
        
        bonds = []
        for _, row in df.iterrows():
            try:
                # Parse credit rating using the new from_string method
                credit_rating = CreditRating.from_string(str(row['CreditRating']))
                
                bond = Bond(
                    isin=str(row['ISIN']),  # Ensure ISIN is string
                    clean_price=float(row['CleanPrice']),
                    ytm=float(row['YTM']),
                    modified_duration=float(row['ModifiedDuration']),
                    maturity_date=pd.to_datetime(row['MaturityDate']).to_pydatetime(),
                    coupon_rate=float(row['CouponRate']),
                    coupon_frequency=int(row['CouponFrequency']),
                    credit_rating=credit_rating,
                    min_piece=float(row['MinPiece']),
                    increment_size=float(row['IncrementSize']),
                    currency=str(row['Currency']),
                    day_count_convention=str(row['DayCountConvention']),
                    issuer=str(row['Issuer'])
                )
                bonds.append(bond)
            except Exception as e:
                error_msg = f"Error loading bond {row.get('ISIN', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                st.error(error_msg)
        
        logger.info(f"Successfully created {len(bonds)} bond objects")
        return bonds
    except Exception as e:
        error_msg = f"Error loading file: {str(e)}"
        logger.exception(error_msg)
        st.error(error_msg)
        return []

def main():
    """Main application entry point"""
    st.title("Bond Portfolio Optimizer")
    
    # Initialize session state
    if 'constraints' not in st.session_state:
        st.session_state.constraints = None
    if 'universe' not in st.session_state:
        st.session_state.universe = None
    if 'optimization_result' not in st.session_state:
        st.session_state.optimization_result = None
    
    # File uploader for bond universe
    st.header("Bond Universe")
    uploaded_file = st.file_uploader("Upload Bond Universe (CSV/Excel)", type=['csv', 'xlsx', 'xls'])
    
    # Load sample universe if no file uploaded
    if uploaded_file is None:
        sample_universe_path = Path(__file__).parent.parent / "data" / "sample_universe_expanded.csv"
        if sample_universe_path.exists():
            logger.info("Loading sample universe")
            uploaded_file = sample_universe_path.open('rb')
            st.info("Using sample bond universe")
    
    # Load bond universe
    if uploaded_file:
        universe = load_bond_universe(uploaded_file)
        if universe:
            st.session_state.universe = universe
            st.success(f"Loaded {len(universe)} bonds")
            
            # Display universe summary with additional columns
            df = pd.DataFrame([{
                'ISIN': bond.isin,
                'Price': f"{bond.clean_price:.2f}",
                'YTM': f"{bond.ytm:.2%}",
                'Duration': f"{bond.modified_duration:.2f}",
                'Maturity': bond.maturity_date.strftime('%Y-%m-%d'),
                'Rating': bond.credit_rating.display(),
                'Issuer': bond.issuer,
                'Min Piece': f"{bond.min_piece:,.0f}",
                'Increment': f"{bond.increment_size:,.0f}"
            } for bond in universe])
            
            # Sort by YTM descending
            df = df.sort_values('YTM', ascending=False)
            st.dataframe(df, hide_index=True)
    
    # Render constraints form
    constraints = render_constraints_form()
    
    # Run optimization if we have both universe and constraints
    if st.session_state.universe and constraints:
        try:
            optimizer = PortfolioOptimizer(st.session_state.universe, constraints)
            result = optimizer.optimize()
            logger.info(f"Optimization completed with status: {result.status}")
            
            if result.success:
                if result.constraints_satisfied:
                    st.success(f"Optimization completed successfully in {result.solve_time:.2f} seconds")
                display_optimization_results(result, st.session_state.universe, constraints.total_size)
                
                # Add download buttons for results
                portfolio_df = pd.DataFrame([{
                    'ISIN': isin,
                    'Weight': weight,
                    'Notional': weight * constraints.total_size,
                    'Bond': next(b for b in st.session_state.universe if b.isin == isin)
                } for isin, weight in result.portfolio.items()])
                
                # Add bond details
                portfolio_df['Issuer'] = portfolio_df['Bond'].apply(lambda x: x.issuer)
                portfolio_df['Rating'] = portfolio_df['Bond'].apply(lambda x: x.credit_rating.display())
                portfolio_df['YTM'] = portfolio_df['Bond'].apply(lambda x: x.ytm)
                portfolio_df['Duration'] = portfolio_df['Bond'].apply(lambda x: x.modified_duration)
                portfolio_df['Min Piece'] = portfolio_df['Bond'].apply(lambda x: x.min_piece)
                portfolio_df['Increment'] = portfolio_df['Bond'].apply(lambda x: x.increment_size)
                
                # Drop Bond column and sort by Weight
                portfolio_df = portfolio_df.drop('Bond', axis=1).sort_values('Weight', ascending=False)
                
                # Format columns
                portfolio_df['Weight'] = portfolio_df['Weight'].apply(lambda x: f"{x:.2%}")
                portfolio_df['Notional'] = portfolio_df['Notional'].apply(lambda x: f"{x:,.0f}")
                portfolio_df['YTM'] = portfolio_df['YTM'].apply(lambda x: f"{x:.2%}")
                portfolio_df['Duration'] = portfolio_df['Duration'].apply(lambda x: f"{x:.2f}")
                portfolio_df['Min Piece'] = portfolio_df['Min Piece'].apply(lambda x: f"{x:,.0f}")
                portfolio_df['Increment'] = portfolio_df['Increment'].apply(lambda x: f"{x:,.0f}")
                
                # Convert to CSV
                csv = portfolio_df.to_csv(index=False)
                st.download_button(
                    label="Download Portfolio as CSV",
                    data=csv,
                    file_name="optimal_portfolio.csv",
                    mime="text/csv"
                )
            else:
                st.error(f"Optimization failed: {result.status}")
                if result.constraint_violations:
                    st.write("Constraint violations:")
                    for violation in result.constraint_violations:
                        st.write(f"- {violation}")
                
        except Exception as e:
            error_msg = f"Optimization error: {str(e)}"
            logger.exception(error_msg)
            st.error(error_msg)

if __name__ == "__main__":
    main()
