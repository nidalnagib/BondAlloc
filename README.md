# Bond Portfolio Optimizer

A streamlit-based web application for optimizing fixed-income portfolios. The optimizer maximizes portfolio yield while satisfying various constraints including duration, credit rating, position sizes, and issuer concentration limits.

## Features

### Portfolio Optimization
- **Objective**: Maximize portfolio yield (YTM)
- **Smart Position Sizing**: Handles minimum piece sizes and increment requirements
- **Rating Management**: Supports full rating scale (AAA to D) with +/- modifiers
- **High Yield Focus**: Specialized constraints for high yield portfolios
- **Constraint Types**:
  - Duration target with tolerance
  - Minimum credit rating requirement
  - Minimum yield target
  - Position size limits (min/max)
  - Number of securities range
  - Maximum issuer exposure
  - High Yield specific constraints

### User Interface
- Clean, modern web interface built with Streamlit
- Interactive constraints form with validation
- Portfolio metrics display (Yield, Duration, Rating, Number of Securities)
- Detailed portfolio composition view with:
  - Target and rounded notionals
  - Position size warnings
  - Minimum piece and increment information
- Rich visualizations:
  - Country allocation pie chart
  - Rating breakdown (detailed and IG/HY)
  - Cash flow distribution using rounded notionals
  - Top 10 issuers and positions
- Downloadable results in CSV format
- Comprehensive error reporting and constraint violation details

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BondAlloc.git
cd BondAlloc
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app/main.py
```

2. Upload your bond universe file (CSV/Excel) with the following columns:
   - ISIN: Bond identifier
   - Issuer: Name of the issuer
   - Rating: Credit rating (e.g., "AAA", "AA+", "BBB-")
   - YTM: Yield to maturity (decimal)
   - Duration: Modified duration
   - Price: Clean price
   - Maturity: Maturity date
   - MinPiece: Minimum investment amount
   - Increment: Increment size for trades
   - Country: Country of risk
   - Currency: Bond currency

3. Set your portfolio constraints:
   - Total portfolio size
   - Duration target and tolerance
   - Minimum rating requirement
   - Position size limits (up to 20%)
   - Number of securities range (up to 15)
   - Maximum issuer exposure (up to 20%)
   - High Yield specific constraints

4. Click "Optimize Portfolio" to run the optimization

5. Review results:
   - Portfolio metrics (target vs rounded size)
   - Detailed position breakdown with notionals
   - Position size warnings and adjustments
   - Cash flow projections based on rounded notionals
   - Geographic and rating distributions
   - Download the complete portfolio as CSV

## Technical Details

### Optimization Method
- Linear programming using CVXPY
- Convex optimization for global optimum
- Smart handling of position size requirements
- Numerical tolerance for constraint satisfaction

### Rating Scale
- Logarithmic scale from AAA (1) to D (22)
- Supports rating modifiers (+/-)
- Portfolio average rating calculated on same scale

### Position Sizing
- Automatic rounding to match increment sizes
- Enforcement of minimum piece requirements
- Warning system for position size violations
- Detailed tracking of target vs rounded allocations

### Logging
- Comprehensive logging to `logs/bondalloc.log`
- Detailed constraint setup and validation logs
- Position size adjustment tracking
- Optimization status and warnings
- Performance metrics and timing information

## Contributing

Feel free to open issues or submit pull requests with improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
