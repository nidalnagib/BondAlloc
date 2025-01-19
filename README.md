# Bond Portfolio Optimizer

A streamlit-based web application for optimizing fixed-income portfolios. The optimizer maximizes portfolio yield while satisfying various constraints including duration, credit rating, position sizes, and issuer concentration limits.

## Features

### Portfolio Optimization
- **Objective**: Maximize portfolio yield (YTM)
- **Smart Position Sizing**: Handles minimum piece sizes and increment requirements
- **Rating Management**: Supports full rating scale (AAA to D) with +/- modifiers
- **Constraint Types**:
  - Duration target with tolerance
  - Minimum credit rating requirement
  - Minimum yield target
  - Position size limits (min/max)
  - Number of securities range
  - Maximum issuer exposure
  - Optional rating bucket constraints

### User Interface
- Clean, modern web interface built with Streamlit
- Interactive constraints form with validation
- Portfolio metrics display (Yield, Duration, Rating, Number of Securities)
- Detailed portfolio composition view with rounded notionals
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

3. Set your portfolio constraints:
   - Total portfolio size
   - Duration target and tolerance
   - Minimum rating requirement
   - Position size limits
   - Number of securities range
   - Maximum issuer exposure
   - Optional rating bucket constraints

4. Click "Optimize Portfolio" to run the optimization

5. Review results:
   - Portfolio metrics
   - Detailed position breakdown
   - Any constraint violations or warnings
   - Download the portfolio as CSV

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

### Logging
- Comprehensive logging to `logs/bondalloc.log`
- Includes optimization status and any errors
- Useful for debugging and audit trail

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
