# Bond Portfolio Optimization Tool

A Streamlit-based application for optimizing bond portfolio construction with advanced constraint handling and natural language processing capabilities.

## Features

- Mixed Integer Quadratic Programming optimization
- Natural language and form-based portfolio requirements input
- Comprehensive constraint handling (duration, yield, credit rating, etc.)
- Interactive visualizations for portfolio analysis
- Detailed reporting and export capabilities

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your ANTHROPIC_API_KEY for Claude integration
   - Configure your preferred solver (MOSEK/GUROBI)

## Project Structure

```
BondAlloc/
├── app/
│   ├── main.py              # Streamlit application entry point
│   ├── optimization/        # Optimization engine
│   ├── data/               # Data handling and processing
│   ├── ui/                 # UI components
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── data/                   # Sample data and schemas
└── docs/                   # Documentation
```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app/main.py
   ```
2. Access the application at http://localhost:8501

## Documentation

Detailed documentation is available in the `docs/` directory:
- User Manual
- API Documentation
- Constraint Specification Guide
- Example Configurations

## License

MIT License
