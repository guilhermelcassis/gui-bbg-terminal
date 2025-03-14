from django import forms
from django.forms import DateInput
from datetime import datetime
from django.core.exceptions import ValidationError

# Top 50 S&P 500 stocks by weight (as of recent data)
TOP_SP500_STOCKS = [
    ('AAPL', 'Apple (AAPL)'),
    ('MSFT', 'Microsoft (MSFT)'),
    ('AMZN', 'Amazon (AMZN)'),
    ('NVDA', 'NVIDIA (NVDA)'),
    ('GOOGL', 'Alphabet Class A (GOOGL)'),
    ('META', 'Meta Platforms (META)'),
    ('GOOG', 'Alphabet Class C (GOOG)'),
    ('TSLA', 'Tesla (TSLA)'),
    ('BRK.B', 'Berkshire Hathaway (BRK.B)'),
    ('LLY', 'Eli Lilly (LLY)'),
    ('AVGO', 'Broadcom (AVGO)'),
    ('UNH', 'UnitedHealth Group (UNH)'),
    ('JPM', 'JPMorgan Chase (JPM)'),
    ('V', 'Visa (V)'),
    ('PG', 'Procter & Gamble (PG)'),
    ('MA', 'Mastercard (MA)'),
    ('HD', 'Home Depot (HD)'),
    ('XOM', 'Exxon Mobil (XOM)'),
    ('MRK', 'Merck (MRK)'),
    ('COST', 'Costco (COST)'),
    ('ABBV', 'AbbVie (ABBV)'),
    ('CVX', 'Chevron (CVX)'),
    ('PEP', 'PepsiCo (PEP)'),
    ('ADBE', 'Adobe (ADBE)'),
    ('KO', 'Coca-Cola (KO)'),
    ('ACN', 'Accenture (ACN)'),
    ('TMO', 'Thermo Fisher Scientific (TMO)'),
    ('MCD', 'McDonald\'s (MCD)'),
    ('BAC', 'Bank of America (BAC)'),
    ('CSCO', 'Cisco Systems (CSCO)'),
    ('CRM', 'Salesforce (CRM)'),
    ('WMT', 'Walmart (WMT)'),
    ('ABT', 'Abbott Laboratories (ABT)'),
    ('NFLX', 'Netflix (NFLX)'),
    ('AMD', 'Advanced Micro Devices (AMD)'),
    ('DHR', 'Danaher (DHR)'),
    ('CMCSA', 'Comcast (CMCSA)'),
    ('PFE', 'Pfizer (PFE)'),
    ('ORCL', 'Oracle (ORCL)'),
    ('TXN', 'Texas Instruments (TXN)'),
    ('INTC', 'Intel (INTC)'),
    ('NKE', 'Nike (NKE)'),
    ('PM', 'Philip Morris (PM)'),
    ('INTU', 'Intuit (INTU)'),
    ('VZ', 'Verizon (VZ)'),
    ('CAT', 'Caterpillar (CAT)'),
    ('IBM', 'IBM (IBM)'),
    ('NOW', 'ServiceNow (NOW)'),
    ('RTX', 'Raytheon Technologies (RTX)'),
    ('AMGN', 'Amgen (AMGN)'),
]

# Top Ibovespa stocks by weight (Brazilian market)
TOP_IBOVESPA_STOCKS = [
    ('PETR4.SA', 'Petrobras PN (PETR4)'),
    ('VALE3.SA', 'Vale ON (VALE3)'),
    ('ITUB4.SA', 'Itaú Unibanco PN (ITUB4)'),
    ('BBDC4.SA', 'Bradesco PN (BBDC4)'),
    ('ABEV3.SA', 'Ambev ON (ABEV3)'),
    ('B3SA3.SA', 'B3 ON (B3SA3)'),
    ('RENT3.SA', 'Localiza ON (RENT3)'),
    ('BBAS3.SA', 'Banco do Brasil ON (BBAS3)'),
    ('WEGE3.SA', 'WEG ON (WEGE3)'),
    ('ITSA4.SA', 'Itaúsa PN (ITSA4)'),
    ('SUZB3.SA', 'Suzano ON (SUZB3)'),
    ('BBSE3.SA', 'BB Seguridade ON (BBSE3)'),
    ('MGLU3.SA', 'Magazine Luiza ON (MGLU3)'),
    ('JBSS3.SA', 'JBS ON (JBSS3)'),
    ('RADL3.SA', 'Raia Drogasil ON (RADL3)'),
    ('UGPA3.SA', 'Ultrapar ON (UGPA3)'),
    ('BRFS3.SA', 'BRF ON (BRFS3)'),
    ('LREN3.SA', 'Lojas Renner ON (LREN3)'),
    ('VIVT3.SA', 'Telefônica Brasil ON (VIVT3)'),
    ('CMIG4.SA', 'Cemig PN (CMIG4)'),
    ('CSAN3.SA', 'Cosan ON (CSAN3)'),
    ('SBSP3.SA', 'Sabesp ON (SBSP3)'),
    ('ENEV3.SA', 'Eneva ON (ENEV3)'),
    ('CIEL3.SA', 'Cielo ON (CIEL3)'),
    ('EMBR3.SA', 'Embraer ON (EMBR3)'),
    ('EGIE3.SA', 'Engie Brasil ON (EGIE3)'),
    ('CCRO3.SA', 'CCR ON (CCRO3)'),
    ('TOTS3.SA', 'Totvs ON (TOTS3)'),
    ('ELET3.SA', 'Eletrobras ON (ELET3)'),
    ('RAIL3.SA', 'Rumo ON (RAIL3)'),
]

class StockSelectionForm(forms.Form):
    # Add a market selector
    market = forms.ChoiceField(
        choices=[
            ('sp500', 'S&P 500 (EUA)'),
            ('ibovespa', 'Ibovespa (Brasil)')
        ],
        widget=forms.RadioSelect(attrs={'class': 'market-selector'}),
        initial='sp500',
        label="Mercado"
    )
    
    # For S&P 500 stocks
    predefined_stocks = forms.MultipleChoiceField(
        choices=TOP_SP500_STOCKS, 
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Top 50 S&P 500 (por peso)",
        help_text="Selecione uma ou mais ações das principais empresas do S&P 500"
    )
    
    # For Ibovespa stocks
    ibovespa_stocks = forms.MultipleChoiceField(
        choices=TOP_IBOVESPA_STOCKS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Top 30 Ibovespa (Brasil)",
        help_text="Selecione uma ou mais ações das principais empresas da B3"
    )
    
    # For custom stock symbols
    custom_stocks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Digite os símbolos separados por vírgula ou espaço (ex: AAPL, MSFT, GOOGL)'
        }),
        label="Símbolos personalizados",
        help_text="Digite os símbolos exatos das ações separados por vírgula ou espaço"
    )
    
    interval = forms.ChoiceField(
        choices=[
            ('1d', 'Último Dia'),
            ('2d', 'Últimos 2 Dias'),
            ('3d', 'Últimos 3 Dias'),
            ('4d', 'Últimos 4 Dias'),
            ('5d', 'Últimos 5 Dias'),
            ('1mo', 'Último Mês'),
            ('6mo', 'Últimos 6 Meses'),
            ('1y', 'Último Ano'),
            ('5y', 'Últimos 5 Anos'),
            ('custom', 'Intervalo Personalizado'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateField(
        widget=DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'max': datetime.now().strftime('%Y-%m-%d')
        }),
        required=False,
        label="Data Inicial"
    )
    
    end_date = forms.DateField(
        widget=DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'max': datetime.now().strftime('%Y-%m-%d')
        }),
        required=False,
        label="Data Final"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize labels and help text
        self.fields['interval'].label = "Período de análise"

    def clean(self):
        cleaned_data = super().clean()
        market = cleaned_data.get('market')
        predefined_stocks = cleaned_data.get('predefined_stocks', [])
        ibovespa_stocks = cleaned_data.get('ibovespa_stocks', [])
        custom_stocks = cleaned_data.get('custom_stocks', '')
        interval = cleaned_data.get('interval')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Process custom stock symbols - but only if custom_stocks is a string
        # This prevents conflicts with clean_custom_stocks method
        custom_stock_symbols = []
        if custom_stocks:
            if isinstance(custom_stocks, str):  # Only process if it's a string
                # Process exactly as entered - no automatic conversions
                for symbol in custom_stocks.replace(',', ' ').split():
                    symbol = symbol.strip().upper()
                    if symbol:  # Skip empty symbols
                        # No automatic suffix or conversions - respect user input
                        custom_stock_symbols.append(symbol)
                        print(f"Added custom stock symbol: {symbol}")
            else:  # It's already a list (processed by clean_custom_stocks)
                custom_stock_symbols = custom_stocks
        
        # Combine BOTH predefined and ibovespa stocks plus custom stocks
        all_stocks = list(predefined_stocks) + list(ibovespa_stocks) + custom_stock_symbols
        
        # Debug logging to verify all stocks being processed
        print(f"All stocks after processing: {all_stocks}")
        print(f"Custom stocks specifically: {custom_stock_symbols}")
        
        # Ensure at least one stock is selected
        if not all_stocks:
            self.add_error(None, 'Selecione pelo menos uma ação para análise. Você pode escolher da lista ou inserir símbolos personalizados.')
        
        # Validate date interval
        if interval == 'custom':
            if not start_date:
                self.add_error('start_date', 'A data inicial é obrigatória para intervalos personalizados.')
            
            if not end_date:
                self.add_error('end_date', 'A data final é obrigatória para intervalos personalizados.')
            
            if start_date and end_date and start_date > end_date:
                self.add_error('start_date', 'A data inicial não pode ser posterior à data final.')
        
        # Store the combined list of stocks
        cleaned_data['stocks'] = all_stocks
        
        return cleaned_data