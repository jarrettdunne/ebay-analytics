import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define theme colors
DARK_THEME = {
    'background': '#1a1a1a',
    'paper': '#2d2d2d',
    'text': '#ffffff',
    'secondary-text': '#a3a3a3',
    'border': '#404040',
    'hover': '#404040',
    'accent': '#3498db'
}

LIGHT_THEME = {
    'background': '#ffffff',
    'paper': '#f5f5f5',
    'text': '#000000',
    'secondary-text': '#666666',
    'border': '#dddddd',
    'hover': '#f0f0f0',
    'accent': '#2980b9'
}

# Layout
app.layout = html.Div([
    # Theme Store
    dcc.Store(id='theme-store', data='light'),
    
    # Main Container
    html.Div(
        id='main-container',
        children=[
            # Header with theme toggle
            html.Div([
                html.H1('eBay Sales Analysis Dashboard', 
                       style={'display': 'inline-block', 'marginRight': '20px'}),
                html.Button(
                    '🌓 Toggle Theme',
                    id='theme-toggle',
                    style={
                        'border': 'none',
                        'padding': '10px 20px',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'marginLeft': '20px'
                    }
                )
            ], style={'textAlign': 'center', 'marginBottom': '30px'}),
            
            # File Upload Component
            html.Div([
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px 0',
                        'cursor': 'pointer',
                    }
                ),
                html.Div(id='upload-status', style={'textAlign': 'center', 'marginBottom': '20px'}),
            ]),
            
            # Hidden div to store the uploaded data
            dcc.Store(id='stored-data'),
            
            # Main Dashboard Content (initially hidden)
            html.Div(
                id='dashboard-content',
                style={'display': 'none'},
                children=[
                    # Feature Selection
                    html.Div([
                        html.H4('Select Features to Display'),
                        dcc.Checklist(
                            id='feature-selector',
                            options=[
                                {'label': ' Transaction Date', 'value': 'Transaction creation date'},
                                {'label': ' Type', 'value': 'Type'},
                                {'label': ' Order Number', 'value': 'Order number'},
                                {'label': ' Net Amount', 'value': 'Net amount'},
                                {'label': ' Item Title', 'value': 'Item title'},
                                {'label': ' Buyer Username', 'value': 'Buyer username'}
                            ],
                            value=['Transaction creation date', 'Net amount', 'Type'],
                            inline=True,
                            className='feature-checklist'
                        )
                    ], className='section-container'),
                    
                    # Filters Section
                    html.Div([
                        html.H4('Filters'),
                        html.Div([
                            # Date Range Filter
                            html.Div([
                                html.Label('Date Range'),
                                dcc.DatePickerRange(
                                    id='date-range',
                                    display_format='YYYY-MM-DD',
                                    style={'marginTop': '5px'}
                                )
                            ], style={'marginRight': '20px'}),
                            
                            # Month-Year Filter
                            html.Div([
                                html.Label('Month/Year Filter'),
                                dcc.Dropdown(
                                    id='month-year-selector',
                                    placeholder='Select Month/Year',
                                    style={
                                        'width': '200px',
                                        'marginTop': '5px'
                                    }
                                )
                            ])
                        ], style={'display': 'flex', 'alignItems': 'flex-start'})
                    ], className='section-container'),
                    
                    # Data Table
                    html.Div([
                        html.H4('Data Sample'),
                        dash_table.DataTable(
                            id='data-table',
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'minWidth': '100px',
                                'maxWidth': '300px',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis'
                            },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            page_size=10,
                            sort_action='native',
                            filter_action='native',
                            derived_virtual_data=[],
                            derived_virtual_indices=[]
                        )
                    ], className='section-container'),
                    
                    # Summary Statistics
                    html.Div([
                        html.H4('Summary Statistics'),
                        html.Div(id='summary-stats', className='row')
                    ], className='section-container'),
                    
                    # Sales Trend Graph
                    html.Div([
                        html.H4('Sales Trend'),
                        dcc.Graph(id='sales-trend')
                    ], className='section-container')
                ]
            )
        ]
    )
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None, f'Unsupported file type: {filename}. Please upload a CSV or Excel file.'
        
        # Convert date column to datetime
        df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
        
        # Convert Net amount to numeric, removing any currency symbols
        df['Net amount'] = pd.to_numeric(df['Net amount'].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
        
        # Replace '--' with None for easier processing
        df['Item title'] = df['Item title'].replace('--', None)
        
        # For each Order number, get the first non-null Item title
        title_mapping = df[
            (df['Order number'].notna()) & 
            (df['Item title'].notna())
        ].groupby('Order number')['Item title'].first()
        
        # Apply the mapping to all rows with matching Order numbers
        df.loc[df['Order number'].notna(), 'Item title'] = df['Order number'].map(title_mapping)
        
        # Replace None back with '--' for display
        df['Item title'] = df['Item title'].fillna('--')
        
        return df, f'Successfully loaded {filename}'
    except Exception as e:
        return None, f'Error processing {filename}: {str(e)}'


# Callback for file upload
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'children'),
     Output('dashboard-content', 'style'),
     Output('date-range', 'start_date'),
     Output('date-range', 'end_date'),
     Output('month-year-selector', 'options')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    if contents is None:
        return None, 'No file uploaded yet.', {'display': 'none'}, None, None, []
    
    df, message = parse_contents(contents, filename)
    
    if df is not None:
        # Create month-year options
        df['month_year'] = df['Transaction creation date'].dt.strftime('%B %Y')
        month_year_options = sorted(
            [{'label': my, 'value': my} for my in df['month_year'].unique()],
            key=lambda x: pd.to_datetime(x['value'], format='%B %Y')
        )
        
        # Store the data as a JSON string
        data = df.to_json(date_format='iso', orient='split')
        start_date = df['Transaction creation date'].min()
        end_date = df['Transaction creation date'].max()
        
        return data, message, {'display': 'block'}, start_date, end_date, month_year_options
    else:
        return None, message, {'display': 'none'}, None, None, []

# Callback for theme toggle
@app.callback(
    [Output('theme-store', 'data'),
     Output('main-container', 'style'),
     Output('data-table', 'style_data'),
     Output('data-table', 'style_header'),
     Output('upload-data', 'style'),
     Output('theme-toggle', 'style')],
    Input('theme-toggle', 'n_clicks'),
    State('theme-store', 'data')
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        current_theme = 'dark'
    else:
        current_theme = 'dark' if current_theme == 'light' else 'light'
    
    theme = DARK_THEME if current_theme == 'dark' else LIGHT_THEME
    
    # Main container style
    container_style = {
        'backgroundColor': theme['background'],
        'color': theme['text'],
        'minHeight': '100vh',
        'padding': '20px'
    }
    
    # Data table styles
    table_data_style = {
        'backgroundColor': theme['paper'],
        'color': theme['text'],
        'border': f'1px solid {theme["border"]}'
    }
    
    table_header_style = {
        'backgroundColor': theme['paper'],
        'color': theme['text'],
        'border': f'1px solid {theme["border"]}',
        'fontWeight': 'bold'
    }
    
    # Upload component style
    upload_style = {
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '10px 0',
        'backgroundColor': theme['paper'],
        'borderColor': theme['border'],
        'color': theme['text']
    }
    
    # Theme toggle button style
    toggle_style = {
        'backgroundColor': theme['paper'],
        'color': theme['text'],
        'border': f'1px solid {theme["border"]}',
        'padding': '10px 20px',
        'borderRadius': '5px',
        'cursor': 'pointer',
        'marginLeft': '20px'
    }
    
    return current_theme, container_style, table_data_style, table_header_style, upload_style, toggle_style

# Callback for Data Table
@app.callback(
    [Output('data-table', 'data'),
     Output('data-table', 'columns')],
    [Input('stored-data', 'data'),
     Input('feature-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('month-year-selector', 'value')]
)
def update_table(stored_data, selected_features, start_date, end_date, selected_month_year):
    if stored_data is None:
        return [], []
    
    df = pd.read_json(stored_data, orient='split')
    df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
    
    # Date filtering
    if start_date and end_date:
        df = df[
            (df['Transaction creation date'] >= start_date) & 
            (df['Transaction creation date'] <= end_date)
        ]
    
    # Month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Transaction creation date'].dt.month == month_year_date.month) &
            (df['Transaction creation date'].dt.year == month_year_date.year)
        ]
    
    # Feature filtering
    df = df[selected_features]
    
    # Format date column
    if 'Transaction creation date' in df.columns:
        df['Transaction creation date'] = df['Transaction creation date'].dt.strftime('%Y-%m-%d')
    
    # Format numeric columns
    if 'Net amount' in df.columns:
        df['Net amount'] = df['Net amount'].round(2)
    
    columns = [{'name': i, 'id': i} for i in df.columns]
    return df.to_dict('records'), columns

# Callback for Summary Statistics
@app.callback(
    Output('summary-stats', 'children'),
    [Input('stored-data', 'data'),
     Input('feature-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('month-year-selector', 'value'),
     Input('data-table', 'derived_virtual_data'),
     Input('data-table', 'derived_virtual_indices')]
)
def update_summary_stats(stored_data, selected_features, start_date, end_date, 
                        selected_month_year, filtered_rows, filtered_indices):
    if stored_data is None:
        return []
    
    # Load initial data
    df = pd.read_json(stored_data, orient='split')
    df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
    
    # Apply date filtering
    if start_date and end_date:
        df = df[
            (df['Transaction creation date'] >= start_date) & 
            (df['Transaction creation date'] <= end_date)
        ]
    
    # Apply month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Transaction creation date'].dt.month == month_year_date.month) &
            (df['Transaction creation date'].dt.year == month_year_date.year)
        ]
    
    # Apply table filtering
    if filtered_rows and filtered_indices:
        df = pd.DataFrame(filtered_rows)
        if 'Transaction creation date' in df.columns:
            df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
        if 'Net amount' in df.columns:
            df['Net amount'] = pd.to_numeric(df['Net amount'], errors='coerce')
    
    stats = []
    
    # Financial Statistics
    if 'Net amount' in selected_features:
        if 'Type' in selected_features:
            # Order revenue
            orders_mask = (df['Type'] == 'Order')
            total_orders = df[orders_mask]['Net amount'].sum()
            avg_order = df[orders_mask]['Net amount'].mean() if len(df[orders_mask]) > 0 else 0
            
            # Refunds
            refunds_mask = (df['Type'] == 'Refund')
            total_refunds = abs(df[refunds_mask]['Net amount'].sum())
            
            # Shipping labels
            shipping_mask = (df['Type'] == 'Shipping label')
            total_shipping = abs(df[shipping_mask]['Net amount'].sum())
            
            # Other fees
            fees_mask = (df['Type'] == 'Other fee')
            total_fees = abs(df[fees_mask]['Net amount'].sum())
            
            # Payouts
            payouts_mask = (df['Type'] == 'Payout')
            total_payouts = df[payouts_mask]['Net amount'].sum()
            
            # Calculate net revenue (Orders - Refunds - Shipping - Fees)
            net_revenue = total_orders - total_refunds - total_shipping - total_fees
            
            stats.extend([
                html.Div([
                    html.H5('Order Revenue'),
                    html.H3(f'${total_orders:,.2f}'),
                    html.P(f'Average: ${avg_order:,.2f}')
                ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Net Revenue'),
                    html.H3(f'${net_revenue:,.2f}'),
                    html.P(f'After fees & refunds')
                ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Expenses'),
                    html.H3(f'${(total_shipping + total_fees):,.2f}'),
                    html.P(f'Shipping: ${total_shipping:,.2f}')
                ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Refunds'),
                    html.H3(f'${total_refunds:,.2f}'),
                    html.P(f'From total orders')
                ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Payouts'),
                    html.H3(f'${total_payouts:,.2f}'),
                    html.P(f'Total transferred')
                ], style={'width': '20%', 'display': 'inline-block', 'textAlign': 'center'})
            ])
        else:
            # If Type is not selected, use simple positive/negative calculation
            total_positive = df[df['Net amount'] > 0]['Net amount'].sum()
            total_negative = abs(df[df['Net amount'] < 0]['Net amount'].sum())
            net_total = total_positive - total_negative
            
            stats.extend([
                html.Div([
                    html.H5('Total Income'),
                    html.H3(f'${total_positive:,.2f}'),
                ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Total Expenses'),
                    html.H3(f'${total_negative:,.2f}'),
                ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'}),
                
                html.Div([
                    html.H5('Net Total'),
                    html.H3(f'${net_total:,.2f}'),
                ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'})
            ])
    
    # Transaction Statistics
    if 'Type' in selected_features:
        type_counts = df['Type'].value_counts()
        total_transactions = len(df)
        
        stats.extend([
            html.Div([
                html.H5('Transaction Breakdown'),
                html.H3(f'{total_transactions:,} Total'),
                html.P(', '.join([f'{k}: {v:,}' for k, v in type_counts.items()]))
            ], style={'width': '50%', 'display': 'inline-block', 'textAlign': 'center'})
        ])
    
    # Buyer Statistics
    if 'Buyer username' in selected_features:
        unique_buyers = df['Buyer username'].nunique()
        repeat_buyers = df.groupby('Buyer username').size()
        repeat_buyer_count = len(repeat_buyers[repeat_buyers > 1])
        repeat_rate = (repeat_buyer_count / unique_buyers * 100) if unique_buyers > 0 else 0
        
        stats.extend([
            html.Div([
                html.H5('Unique Buyers'),
                html.H3(f'{unique_buyers:,}'),
                html.P(f'Total distinct customers')
            ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'}),
            
            html.Div([
                html.H5('Repeat Buyers'),
                html.H3(f'{repeat_buyer_count:,}'),
                html.P(f'{repeat_rate:.1f}% of total buyers')
            ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'})
        ])
    
    # Time Period Statistics
    if 'Transaction creation date' in selected_features:
        date_range = (df['Transaction creation date'].max() - df['Transaction creation date'].min()).days
        daily_avg_transactions = len(df) / (date_range + 1) if date_range >= 0 else len(df)
        
        stats.extend([
            html.Div([
                html.H5('Time Period'),
                html.H3(f'{date_range + 1} days'),
                html.P(f'{daily_avg_transactions:.1f} transactions/day')
            ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'})
        ])
    
    return html.Div(stats, style={'marginBottom': '20px', 'marginTop': '20px'})
# Callback for Sales Trend
@app.callback(
    Output('sales-trend', 'figure'),
    [Input('stored-data', 'data'),
     Input('feature-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('month-year-selector', 'value'),
     Input('data-table', 'derived_virtual_data'),
     Input('data-table', 'derived_virtual_indices'),
     Input('theme-store', 'data')]
)
def update_sales_trend(stored_data, selected_features, start_date, end_date, 
                      selected_month_year, filtered_rows, filtered_indices, theme):
    if stored_data is None or 'Transaction creation date' not in selected_features or 'Net amount' not in selected_features:
        return go.Figure()
    
    # Load and process data
    df = pd.read_json(stored_data, orient='split')
    df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
    
    # Apply date filtering
    if start_date and end_date:
        df = df[
            (df['Transaction creation date'] >= start_date) & 
            (df['Transaction creation date'] <= end_date)
        ]
    
    # Apply month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Transaction creation date'].dt.month == month_year_date.month) &
            (df['Transaction creation date'].dt.year == month_year_date.year)
        ]
    
    # Apply table filtering
    if filtered_rows and filtered_indices:
        df = pd.DataFrame(filtered_rows)
        df['Transaction creation date'] = pd.to_datetime(df['Transaction creation date'])
        df['Net amount'] = pd.to_numeric(df['Net amount'], errors='coerce')
    
    # Group by date and calculate daily sales
    daily_sales = df.groupby('Transaction creation date')['Net amount'].sum().reset_index()
    
    # Calculate moving average for trend line
    daily_sales['MA7'] = daily_sales['Net amount'].rolling(window=7, min_periods=1).mean()
    
    # Set theme-specific colors
    theme_colors = DARK_THEME if theme == 'dark' else LIGHT_THEME
    
    # Create the figure
    fig = go.Figure()
    
    # Add the bar chart
    fig.add_trace(go.Bar(
        x=daily_sales['Transaction creation date'],
        y=daily_sales['Net amount'],
        name='Daily Sales',
        marker_color=theme_colors['accent']
    ))
    
    # Add the moving average trend line
    fig.add_trace(go.Scatter(
        x=daily_sales['Transaction creation date'],
        y=daily_sales['MA7'],
        mode='lines',
        name='7-Day Average',
        line=dict(
            color='rgba(255, 165, 0, 0.7)',
            width=2
        )
    ))
    
    # Update layout with theme colors and improved formatting
    title_text = 'Daily Sales Trend'
    if selected_month_year:
        title_text += f' - {selected_month_year}'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(color=theme_colors['text'])
        ),
        plot_bgcolor=theme_colors['paper'],
        paper_bgcolor=theme_colors['background'],
        font_color=theme_colors['text'],
        xaxis=dict(
            title='Date',
            gridcolor=theme_colors['border'],
            zerolinecolor=theme_colors['border'],
            tickformat='%Y-%m-%d'
        ),
        yaxis=dict(
            title='Sales ($)',
            gridcolor=theme_colors['border'],
            zerolinecolor=theme_colors['border'],
            tickformat='$,.2f'
        ),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0)'
        ),
        hovermode='x unified',
        bargap=0.2
    )
    
    # Add range slider
    fig.update_xaxes(rangeslider_visible=True)
    
    return fig

# Add CSS for smooth theme transitions
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                transition: background-color 0.3s ease, color 0.3s ease;
            }
            .section-container {
                margin-bottom: 30px;
                padding: 20px;
                border-radius: 5px;
            }
            .feature-checklist label {
                margin-right: 20px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run_server(debug=True)