from django.shortcuts import render, HttpResponse
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from .forms import StockSelectionForm
import openpyxl

# Create your views here.
def get_date_range(interval):
    today = datetime.today()
    
    # For custom intervals, we need to fetch enough trading days
    # Trading days are roughly 252 per year (5 days per week, minus holidays)
    intervals = {
        '1d': 5,      # For 1 day, we fetch 5 calendar days to ensure we get at least 1 trading day
        '2d': 5,      # For 2d (which shows 1 day), same as 1d
        '3d': 7,      # For 3d (which shows 2 days), we need at least 2 trading days
        '4d': 9,      # For 4d (which shows 3 days), we need at least 3 trading days
        '5d': 11,     # For 5d (which shows 4 days), we need at least 4 trading days
        '1mo': 45,    # For 1 month, get 45 calendar days (to ensure ~21 trading days)
        '6mo': 190,   # For 6 months, get extra days for holidays
        '1y': 380,    # For 1 year, get extra days for holidays
        '5y': 1900,   # For 5 years, get extra days for holidays
    }
    
    # Get how many calendar days to fetch to ensure we have enough trading data
    fetch_days = intervals.get(interval, 300)
    
    # Get how many trading days we actually want to show
    trading_days = {
        '1d': 2,      # Last 1 trading day 
        '2d': 3,      # When user selects 2d, show 1 day (as per user's request)
        '3d': 4,      # When user selects 3d, show 2 days
        '4d': 5,      # When user selects 4d, show 3 days
        '5d': 6,      # When user selects 5d, show 4 days
        '1mo':21,    # Approximately 21 trading days in a month
        '6mo': 126,   # Approximately 126 trading days in 6 months
        '1y': 252,    # Approximately 252 trading days in a year
        '5y': 1260,   # Approximately 1260 trading days in 5 years
    }.get(interval, -1)  # -1 means use all available data
    
    # Calculate start date with enough buffer to get the required trading days
    start_date = today - timedelta(days=fetch_days)
        
    return start_date, today, trading_days  # Return the fetch period and requested trading days

def stock_analysis(request):
    # Better form initialization with debug info
    if request.method == 'POST':
        form = StockSelectionForm(request.POST)
        # Debug logging
        print(f"Form POST data: {request.POST}")
        print(f"Predefined stocks in POST: {request.POST.getlist('predefined_stocks')}")
        print(f"Ibovespa stocks in POST: {request.POST.getlist('ibovespa_stocks')}")
        print(f"Custom stocks in POST: {request.POST.get('custom_stocks', '')}")
    else:
        form = StockSelectionForm()
        
    chart_html = None  # Initialize chart_html to None

    if request.method == 'POST' and form.is_valid():
        # Log the cleaned data stocks for debugging
        print(f"Processed stocks: {form.cleaned_data['stocks']}")
        
        # Get the list of selected stocks ensuring no duplicates
        selected_stocks = list(set(form.cleaned_data['stocks']))  # Remove any duplicates
        
        # Make sure to include all stocks including custom ones
        print(f"Selected stocks to plot: {selected_stocks}")
        
        if not selected_stocks:
            return render(request, 'stocks/error.html', {
                'error_message': 'Nenhuma ação foi selecionada. Por favor, selecione pelo menos uma ação para análise.'
            })
            
        interval = form.cleaned_data['interval']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Use custom dates if 'custom' interval is selected
        if interval == 'custom' and start_date and end_date:
            # Ensure start_date and end_date are datetime objects
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())
            # For custom dates, we don't use trading_days limit
            trading_days = -1
        else:
            # Use predefined interval
            start_date, end_date, trading_days = get_date_range(interval)

        # Create a user-friendly interval description
        interval_description = {
            '1d': 'Último Dia',
            '2d': 'Último Dia',     # Same as 1d per user's request
            '3d': 'Últimos 2 Dias',  # Show 2 days when user selects 3d
            '4d': 'Últimos 3 Dias',  # Show 3 days when user selects 4d
            '5d': 'Últimos 4 Dias',  # Show 4 days when user selects 5d
            '1mo': 'Último Mês',
            '6mo': 'Últimos 6 Meses',
            '1y': 'Último Ano',
            '5y': 'Últimos 5 Anos',
            'custom': f'De {start_date.strftime("%d/%b/%Y")} até {end_date.strftime("%d/%b/%Y")}',
        }.get(interval, 'Período Personalizado')

        # Collecting data from yfinance and measuring performance
        data_frames = []
        performance_data = {}  # Dictionary to hold performance data
        error_messages = []
        processed_symbols = []  # Keep track of symbols we've actually processed
        
        print(f"About to fetch data for these symbols: {selected_stocks}")
        
        for symbol in selected_stocks:
            try:
                print(f"Processing symbol: {symbol}")
                stock = yf.Ticker(symbol)
                hist = stock.history(start=start_date, end=end_date, auto_adjust=True)
                
                # Skip empty data, but be more lenient with short time intervals
                if hist.empty:
                    print(f"No data returned for {symbol}")
                    error_messages.append(f"Dados insuficientes para {symbol} no período selecionado.")
                    continue
                elif interval in ['1d', '2d', '3d', '4d'] and len(hist) < 1:
                    # For very short intervals, accept even a single data point
                    print(f"Insufficient data for {symbol} in short interval: {len(hist)} rows")
                    error_messages.append(f"Dados insuficientes para {symbol} no período selecionado.")
                    continue
                elif interval not in ['1d', '2d', '3d', '4d'] and len(hist) < 3:
                    # For longer intervals, maintain the 3 data points minimum
                    print(f"Insufficient data for {symbol}: {len(hist)} rows")
                    error_messages.append(f"Dados insuficientes para {symbol} no período selecionado.")
                    continue
                    
                # Ensure we have price changes
                if hist['Close'].max() == hist['Close'].min():
                    error_messages.append(f"{symbol} não apresentou variação no período selecionado.")
                    continue
                    
                # Calculate normalized performance
                hist['Normalized'] = hist['Close']  # Store the real close values, we'll normalize later
                hist['Symbol'] = symbol
                
                # Convert to DataFrame with explicit date column for better handling
                df = hist.reset_index()[['Date', 'Close', 'Normalized', 'Symbol']]
                
                # Ensure data is properly sorted by date
                df = df.sort_values('Date')
                
                # Add to our collection and record this symbol as processed
                data_frames.append(df)
                processed_symbols.append(symbol)
                
                # Calculate performance percentage
                performance_percentage = df['Normalized'].iloc[-1]
                performance_data[symbol] = performance_percentage
                
            except Exception as e:
                error_messages.append(f"Erro ao buscar dados para {symbol}: {str(e)}")
                continue
            
        if not data_frames:
            error_message = 'Nenhum dado válido encontrado para as ações selecionadas no período informado. '
            if error_messages:
                error_message += f'Detalhes dos erros: {"; ".join(error_messages)}'
            return render(request, 'stocks/error.html', {'error_message': error_message})

        # Create combined dataframe only from stocks we successfully processed
        combined_df = pd.concat(data_frames)
        
        # For regular intervals (not custom), limit to exact number of trading days
        if trading_days > 0:
            print(f"Limiting data to last {trading_days} trading days")
            
            # Process each stock separately to get exact trading days
            filtered_dfs = []
            
            for symbol in processed_symbols:
                # Get data for this symbol
                symbol_df = combined_df[combined_df['Symbol'] == symbol]
                
                if len(symbol_df) > 0:
                    # Sort by date, descending (newest first)
                    symbol_df = symbol_df.sort_values('Date', ascending=False)
                    
                    # Keep only the requested number of trading days
                    # If we have fewer days than requested, keep all we have
                    if len(symbol_df) > trading_days:
                        symbol_df = symbol_df.iloc[:trading_days]
                    
                    # Resort by date, ascending for the chart (oldest first)
                    symbol_df = symbol_df.sort_values('Date')
                    
                    # Recalculate normalized performance based ONLY on these days
                    if len(symbol_df) > 0:
                        base_value = symbol_df['Normalized'].iloc[0]  # First day's close price
                        # Keep the original Close price intact while calculating performance
                        symbol_df['Normalized'] = ((symbol_df['Normalized'] - base_value) / base_value) * 100
                    
                    # Add to our filtered dataframes
                    filtered_dfs.append(symbol_df)
            
            # Create new combined dataframe with the filtered data
            if filtered_dfs:
                combined_df = pd.concat(filtered_dfs)
                print(f"Data limited to {len(combined_df)} rows across {len(filtered_dfs)} symbols")
            else:
                print("No data remained after filtering to exact trading days")
        
        # Recalculate performance percentages after filtering
        performance_data = {}
        for symbol in processed_symbols:
            symbol_df = combined_df[combined_df['Symbol'] == symbol]
            if len(symbol_df) > 0:
                # Get the last day's performance percentage
                performance_percentage = symbol_df['Normalized'].iloc[-1]
                performance_data[symbol] = performance_percentage
        
        # Sort by performance for better visualization
        sorted_performance = sorted(performance_data.items(), key=lambda x: x[1], reverse=True)
        sorted_symbols = [symbol for symbol, _ in sorted_performance]

        # Create title with accurate count of stocks actually shown
        chart_title = f'Análise de Desempenho: {len(processed_symbols)} Ações - {interval_description}'

        # Also include a list of successfully processed symbols in the chart description
        symbol_list = ", ".join(processed_symbols)
        chart_subtitle = f'Símbolos processados: {symbol_list}'

        # Define colors for the chart - Bloomberg-inspired colors
        colors = ['#ff8000', '#00c853', '#2196f3', '#f44336', '#9c27b0', '#ff9800', '#03a9f4', '#e91e63', '#3f51b5', '#009688']

        # Create a dataframe that's sorted by performance for better visualization
        # This helps ensure traces appear in order of performance
        sorted_df = pd.DataFrame()
        for symbol in sorted_symbols:
            symbol_df = combined_df[combined_df['Symbol'] == symbol].copy()
            sorted_df = pd.concat([sorted_df, symbol_df])

        # Plotting chart with Plotly - use the sorted dataframe
        fig = px.line(
            sorted_df,
            x='Date',
            y='Normalized',
            color='Symbol',
            title=f"{chart_title}",  # We'll format the title differently below
            labels={'Date': 'Data', 'Normalized': 'Desempenho (%)'},
            template='plotly_dark',
            color_discrete_sequence=colors,
            category_orders={"Symbol": sorted_symbols}  # This ensures the legend is ordered
        )

        # Update the legend labels to include performance percentages (2 decimal places)
        for i, trace in enumerate(fig.data):
            symbol = trace.name
            perf = performance_data[symbol]
            # Format with exactly 2 decimal places
            formatted_perf = f"{perf:.2f}".rstrip('0').rstrip('.') if '.' in f"{perf:.2f}" else f"{perf:.2f}"
            
            # Add + sign for positive values
            if perf > 0:
                formatted_perf = f"+{formatted_perf}"
                
            # Format name with performance and add color indicators
            trace.name = f"{symbol} ({formatted_perf}%)"
            
            # Set line thickness based on performance (better performers get thicker lines)
            relative_thickness = 1.5
            if len(sorted_symbols) > 1:
                # Calculate position in the performance ranking
                rank = sorted_symbols.index(symbol)
                if rank == 0:  # Top performer
                    relative_thickness = 3
                elif rank == 1 and len(sorted_symbols) > 2:  # Second performer
                    relative_thickness = 2.5
                elif rank == len(sorted_symbols) - 1:  # Worst performer
                    relative_thickness = 1
            
            # Set line style
            trace.line = dict(
                width=relative_thickness,
                dash='solid',
            )
            
            # Improve hover template to show only 2 decimal places
            trace.hovertemplate = (
                '<b>%{fullData.name}</b><br>' +
                'Data: %{x|%d/%m/%Y}<br>' +
                'Desempenho: %{y:.2f}%<extra></extra>'
            )

        # Enhance chart appearance for Bloomberg terminal look
        fig.update_layout(
            xaxis_title='Data',
            yaxis_title='Desempenho (%)',
            legend_title='SÍMBOLOS',
            font=dict(family="Roboto Mono, monospace", size=10, color="#f5f5f5"),
            plot_bgcolor='#0c0c0c',
            paper_bgcolor='#0c0c0c',
            hoverlabel=dict(
                font_size=12, 
                font_family="Roboto Mono, monospace",
                bgcolor="#101010",
                bordercolor="#ff8000"
            ),
            hovermode="x unified",
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                traceorder="normal",
                font=dict(family="Roboto Mono, monospace", size=10, color="#f5f5f5"),
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="#333",
                borderwidth=1
            ),
            title=dict(
                text="<span style='font-size:14px;font-weight:700;letter-spacing:0.5px;color:#ff8000;'>ANÁLISE DE PERFORMANCE</span><br>" +
                     f"<span style='font-size:11px;color:#cccccc;'>{len(processed_symbols)} Ações | {interval_description}</span>",
                y=0.98,
                x=0.01,
                xanchor='left',
                yanchor='top',
                font=dict(family="Roboto Mono, monospace")
            ),
            margin=dict(l=60, r=100, t=80, b=50),
            height=550,
            xaxis=dict(
                title=dict(
                    text="DATA",
                    font=dict(family="Roboto Mono, monospace", size=10, color="#999")
                ),
                tickfont=dict(family="Roboto Mono, monospace", size=9),
                gridcolor='rgba(50, 50, 50, 0.2)',
                zerolinecolor='rgba(80, 80, 80, 0.6)',
                showgrid=True
            ),
            yaxis=dict(
                title=dict(
                    text="PERFORMANCE (%)",
                    font=dict(family="Roboto Mono, monospace", size=10, color="#999")
                ),
                tickfont=dict(family="Roboto Mono, monospace", size=9),
                gridcolor='rgba(50, 50, 50, 0.2)',
                zerolinecolor='rgba(80, 80, 80, 0.6)',
                showgrid=True,
                zeroline=True
            )
        )
        
        # Add zero line for reference
        fig.add_hline(y=0, line_width=1, line_dash="solid", line_color="#444444")
        
        # Add vertical gridlines
        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(50, 50, 50, 0.2)',
            gridwidth=1
        )
        
        # Add annotations for top and bottom performers
        if len(sorted_symbols) > 1:
            top_symbol = sorted_symbols[0]
            bottom_symbol = sorted_symbols[-1]
            
            top_df = sorted_df[sorted_df['Symbol'] == top_symbol]
            bottom_df = sorted_df[sorted_df['Symbol'] == bottom_symbol]
            
            top_perf = performance_data[top_symbol]
            bottom_perf = performance_data[bottom_symbol]
            
            # Format performance values
            top_perf_str = f"+{top_perf:.2f}%" if top_perf > 0 else f"{top_perf:.2f}%"
            bottom_perf_str = f"+{bottom_perf:.2f}%" if bottom_perf > 0 else f"{bottom_perf:.2f}%"
            
            # Add annotation for top performer at the last point
            fig.add_annotation(
                x=top_df['Date'].iloc[-1],
                y=top_df['Normalized'].iloc[-1],
                text=f"<b>{top_symbol}</b> {top_perf_str}",
                showarrow=True,
                arrowhead=3,
                arrowcolor="#00c853",
                arrowsize=0.8,
                arrowwidth=1.5,
                ax=40,
                ay=-30,
                font=dict(family="Roboto Mono", size=10, color="#00c853"),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor="#00c853",
                borderwidth=1,
                borderpad=4
            )
            
            # Add annotation for bottom performer at the last point
            fig.add_annotation(
                x=bottom_df['Date'].iloc[-1],
                y=bottom_df['Normalized'].iloc[-1],
                text=f"<b>{bottom_symbol}</b> {bottom_perf_str}",
                showarrow=True,
                arrowhead=3,
                arrowcolor="#ff3d00",
                arrowsize=0.8,
                arrowwidth=1.5,
                ax=40,
                ay=30,
                font=dict(family="Roboto Mono", size=10, color="#ff3d00"),
                bgcolor="rgba(0,0,0,0.7)",
                bordercolor="#ff3d00",
                borderwidth=1,
                borderpad=4
            )
        
        # Make chart responsive
        fig.update_layout(
            autosize=True
        )
        
        # Add a watermark
        fig.add_annotation(
            text="BLOOMBERG STYLE",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(
                family="Roboto Mono",
                size=40,
                color="rgba(255,128,0,0.04)"
            ),
            align="center",
            opacity=0.5,
            textangle=30
        )
        
        # Store the data in session for potential download
        # We'll convert the dataframe to a dictionary that can be serialized
        # First, create a copy and convert the Date column to string to make it JSON serializable
        session_df = sorted_df.copy()
        
        # Check if Date column is datetime type before using .dt accessor
        
        # This makes the code more robust against errors
        if 'Date' in session_df.columns:
            # Convert to string format in a safe way that works regardless of current type
            session_df['Date'] = session_df['Date'].astype(str)
        
        # Ensure we have all required columns for the download
        required_columns = ['Date', 'Symbol', 'Close', 'Normalized']
        for col in required_columns:
            if col not in session_df.columns:
                # If a column is missing, add a placeholder (should never happen, but just in case)
                print(f"Warning: {col} column is missing from the data. Adding placeholder.")
                if col == 'Close':
                    # For Close, use the base price (which we don't directly have, so use a placeholder)
                    session_df[col] = 0.0
                else:
                    session_df[col] = "N/A"
        
        session_data = {
            'chart_data': session_df.to_dict('records'),
            'chart_title': chart_title,
            'interval': interval,
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        request.session['chart_data'] = session_data
        
        # Generate chart HTML
        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        
        # Add download button via JavaScript injection - Bloomberg style
        download_button = """
        <div style="position: absolute; top: 10px; right: 10px; z-index: 1000; display: flex; gap: 5px;">
            <a href="/stocks/download-csv/" class="btn btn-sm" 
               style="background-color: #000; color: #ff8000; border: 1px solid #333; font-family: 'Roboto Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; display: flex; align-items: center;" 
               title="Download CSV" target="_blank">
                <i class="bi bi-file-earmark-arrow-down" style="margin-right: 5px;"></i> CSV
            </a>
            <a href="/stocks/download-excel/" class="btn btn-sm" 
               style="background-color: #000; color: #00c853; border: 1px solid #333; font-family: 'Roboto Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; display: flex; align-items: center;" 
               title="Download Excel" target="_blank">
                <i class="bi bi-file-earmark-excel" style="margin-right: 5px;"></i> XLS
            </a>
            <button type="button" class="btn btn-sm" 
                   style="background-color: #000; color: #9c27b0; border: 1px solid #333; font-family: 'Roboto Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; display: flex; align-items: center;"
                   title="Download as PNG" onclick="downloadChartAsPNG()">
                <i class="bi bi-file-earmark-image" style="margin-right: 5px;"></i> PNG
            </button>
            <button type="button" class="btn btn-sm" 
                   style="background-color: #000; color: #2196f3; border: 1px solid #333; font-family: 'Roboto Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 3px 8px; display: flex; align-items: center;"
                   title="Print Chart Only" onclick="printChartOnly()">
                <i class="bi bi-printer" style="margin-right: 5px;"></i> Print
            </button>
        </div>
        
        <!-- Bloomberg-style time indicator -->
        <div style="position: absolute; top: 10px; left: 10px; z-index: 1000; font-family: 'Roboto Mono', monospace; font-size: 10px; color: #999; background-color: rgba(0,0,0,0.7); padding: 3px 6px; border: 1px solid #333;">
            <span id="live-time">--:--:--</span>
        </div>
        
        <!-- JavaScript functions for the buttons -->
        <script>
            // Update time display
            function updateTime() {
                const now = new Date();
                const hours = now.getHours().toString().padStart(2, '0');
                const minutes = now.getMinutes().toString().padStart(2, '0');
                const seconds = now.getSeconds().toString().padStart(2, '0');
                document.getElementById('live-time').textContent = hours + ':' + minutes + ':' + seconds;
            }
            setInterval(updateTime, 1000);
            updateTime();
            
            // Function to print only the chart
            function printChartOnly() {
                // Get the chart's HTML element
                const chartDiv = document.querySelector('.js-plotly-plot');
                if (!chartDiv) return;
                
                // Create a new window
                const printWindow = window.open('', '_blank');
                
                // Write HTML without using template literals
                printWindow.document.write('<html>');
                printWindow.document.write('<head>');
                printWindow.document.write('<title>Stock Performance Chart</title>');
                printWindow.document.write('<style>');
                printWindow.document.write('body { margin: 0; padding: 10px; background-color: #0c0c0c; }');
                printWindow.document.write('.chart-container { width: 100%; height: 100%; }');
                printWindow.document.write('</style>');
                printWindow.document.write('</head>');
                printWindow.document.write('<body>');
                printWindow.document.write('<div class="chart-container">');
                printWindow.document.write(chartDiv.outerHTML);
                printWindow.document.write('</div>');
                printWindow.document.write('<script src="https://cdn.plot.ly/plotly-latest.min.js"><\/script>');
                printWindow.document.write('<script>');
                printWindow.document.write('setTimeout(function() { window.print(); }, 500);');
                printWindow.document.write('<\/script>');
                printWindow.document.write('</body>');
                printWindow.document.write('</html>');
                
                printWindow.document.close();
            }
            
            // Function to download chart as PNG
            function downloadChartAsPNG() {
                // Find the chart element
                const chartDiv = document.querySelector('.js-plotly-plot');
                if (!chartDiv) return;
                
                // Use Plotly's toImage function
                Plotly.toImage(chartDiv, {
                    format: 'png',
                    width: 1200,
                    height: 800,
                    scale: 2  // Higher resolution
                }).then(function(dataUrl) {
                    // Create a download link
                    const downloadLink = document.createElement('a');
                    downloadLink.href = dataUrl;
                    downloadLink.download = 'stock_performance_chart.png';
                    
                    // Append to document, click it, and remove it
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                });
            }
        </script>
        """
        chart_html = download_button + chart_html

    return render(request, 'stocks/select.html', {'form': form, 'chart_html': chart_html})

def download_chart_data(request, format_type='csv'):
    """
    Download the chart data as CSV or Excel
    """
    # Get the data from session
    session_data = request.session.get('chart_data', None)
    
    if not session_data:
        return HttpResponse("No data available for download. Please generate a chart first.")
    
    # Create the filename based on chart title and timestamp
    timestamp = session_data.get('timestamp', datetime.now().strftime('%Y%m%d_%H%M%S'))
    interval = session_data.get('interval', 'custom')
    filename = f"stock_performance_{interval}_{timestamp}"
    
    # Convert the data back to a DataFrame
    df = pd.DataFrame(session_data.get('chart_data', []))
    
    # If we have an empty dataframe, return an error
    if df.empty:
        return HttpResponse("No data available for download.")
    
    # Rename columns to the user's preferred format in Portuguese
    df = df.rename(columns={
        'Date': 'Data',
        'Symbol': 'Ticker da Acao',
        'Close': 'Preco de Fechamento',
        'Normalized': 'Rentabilidade (%)'
    })
    
    # Ensure columns are in the desired order
    column_order = ['Data', 'Ticker da Acao', 'Preco de Fechamento', 'Rentabilidade (%)']
    df = df[column_order]
    
    response = None
    
    if format_type == 'csv':
        # Create a CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        df.to_csv(path_or_buf=response, index=False)
    
    elif format_type == 'excel':
        try:
            # Try to import openpyxl to check if it's available           
            # Create an Excel response
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
            
            # Create Excel writer
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Desempenho das Ações')
        
        except ImportError:
            # If openpyxl is not available, return a user-friendly error message
            return HttpResponse(
                "Para baixar em formato Excel, é necessário instalar a biblioteca 'openpyxl'. "
                "Por favor, utilize o formato CSV como alternativa ou contate o administrador do sistema para instalar a biblioteca necessária. "
                f"<br><br><a href='/stocks/download-csv/' class='btn btn-primary'>Baixar em CSV</a>",
                content_type='text/html'
            )
    
    return response
            
