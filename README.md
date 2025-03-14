# Stock Analysis Platform - Bloomberg Style

A Django-based stock analysis application designed to visualize and compare the performance of multiple stocks over different time periods. The interface is inspired by Bloomberg terminals, featuring a dark theme and professional financial data visualization.

![Bloomberg-Style Stock Analyzer](https://via.placeholder.com/800x400?text=Bloomberg+Style+Stock+Analyzer)

## Features

- **Multi-Stock Comparison**: Compare performance of multiple stocks on a single chart
- **Flexible Time Periods**: Analyze stocks over standard intervals (1d, 5d, 1mo, 6mo, 1y, 5y) or custom date ranges
- **Major Market Support**: Choose stocks from S&P 500, Ibovespa, or add custom symbols
- **Performance Analysis**: Shows percentage gains/losses with visual indicators
- **Bloomberg Terminal Interface**: Dark theme, terminal-style UI with ticker tape
- **Export Options**:
  - Download data as CSV or Excel
  - Export charts as high-resolution PNG images
  - Print charts directly

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Setup Steps

1. **Clone the repository** (or download ZIP):
   ```bash
   git clone https://github.com/yourusername/stock-analysis.git
   cd stock-analysis
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv myenv
   myenv\Scripts\activate

   # macOS/Linux
   python -m venv myenv
   source myenv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application** at `http://127.0.0.1:8000/`

## Usage

1. **Select Stocks**:
   - Choose from predefined lists (S&P 500, Ibovespa)
   - Add custom stock symbols (use Yahoo Finance notation, e.g., AAPL, MSFT, VALE3.SA)

2. **Set Time Period**:
   - Select from predefined periods or
   - Choose custom date range

3. **Generate Analysis**:
   - Click "Analisar" to generate the performance comparison chart

4. **Export/Share Results**:
   - Download data as CSV/Excel
   - Save chart as PNG
   - Print chart

## Data Source

Stock data is retrieved from Yahoo Finance using the `yfinance` Python package. The application requires an internet connection to fetch real-time and historical stock data.

## Project Structure

```
stock_analysis/
├── manage.py
├── requirements.txt
├── README.md
├── stock_analysis/  # Project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── stocks/          # Main application
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── static/
    └── templates/
```

## Customization

- Modify stock lists in `forms.py`
- Adjust chart colors and styling in `views.py`
- Change UI elements in templates and CSS

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Plotly](https://plotly.com/) for interactive charts
- [yfinance](https://github.com/ranaroussi/yfinance) for stock data
- [Bootstrap](https://getbootstrap.com/) for UI components
- Bloomberg Terminal for design inspiration 