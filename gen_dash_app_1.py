import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
import json

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

# Define numeric columns globally
numeric_columns = [
    'eBay collected tax', 'Item price', 'Quantity', 'Item subtotal',
    'Shipping and handling', 'Seller collected tax', 'Discount',
    'Gross amount', 'Final Value Fee - fixed', 'Final Value Fee - variable',
    'Below standard performance fee', 'Very high "item not as described" fee',
    'International fee', 'Deposit processing fee', 'Regulatory operating fee',
    'Promoted Listing Standard fee', 'Charity donation', 'Shipping labels',
    'Payment Dispute Fee', 'Expenses', 'Refunds', 'Order earnings'
]

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
                        'margin': '10px 0'
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
                                {'label': ' Order Date', 'value': 'Order creation date'},
                                {'label': ' Order Number', 'value': 'Order number'},
                                {'label': ' Item ID', 'value': 'Item ID'},
                                {'label': ' Item Title', 'value': 'Item title'},
                                {'label': ' Buyer Name', 'value': 'Buyer name'},
                                {'label': ' Ship to City', 'value': 'Ship to city'},
                                {'label': ' Ship to State', 'value': 'Ship to province/region/state'},
                                {'label': ' Ship to Zip', 'value': 'Ship to zip'},
                                {'label': ' Ship to Country', 'value': 'Ship to country'},
                                {'label': ' Currency', 'value': 'Transaction currency'},
                                {'label': ' eBay Tax', 'value': 'eBay collected tax'},
                                {'label': ' Item Price', 'value': 'Item price'},
                                {'label': ' Quantity', 'value': 'Quantity'},
                                {'label': ' Item Subtotal', 'value': 'Item subtotal'},
                                {'label': ' Shipping Cost', 'value': 'Shipping and handling'},
                                {'label': ' Seller Tax', 'value': 'Seller collected tax'},
                                {'label': ' Discount', 'value': 'Discount'},
                                {'label': ' Payout Currency', 'value': 'Payout currency'},
                                {'label': ' Gross Amount', 'value': 'Gross amount'},
                                {'label': ' FVF Fixed', 'value': 'Final Value Fee - fixed'},
                                {'label': ' FVF Variable', 'value': 'Final Value Fee - variable'},
                                {'label': ' Below Standard Fee', 'value': 'Below standard performance fee'},
                                {'label': ' INAD Fee', 'value': 'Very high "item not as described" fee'},
                                {'label': ' International Fee', 'value': 'International fee'},
                                {'label': ' Processing Fee', 'value': 'Deposit processing fee'},
                                {'label': ' Operating Fee', 'value': 'Regulatory operating fee'},
                                {'label': ' Promoted Fee', 'value': 'Promoted Listing Standard fee'},
                                {'label': ' Charity', 'value': 'Charity donation'},
                                {'label': ' Shipping Labels', 'value': 'Shipping labels'},
                                {'label': ' Dispute Fee', 'value': 'Payment Dispute Fee'},
                                {'label': ' Expenses', 'value': 'Expenses'},
                                {'label': ' Refunds', 'value': 'Refunds'},
                                {'label': ' Order Earnings', 'value': 'Order earnings'}
                            ],
                            value=['Order creation date', 'Order number', 'Item title', 'Gross amount', 'Order earnings'],
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
                        ),
                        html.Div([
                            html.Button(
                                'Export Processed Data', 
                                id='export-button',
                                style={
                                    'marginTop': '10px',
                                    'padding': '10px 20px',
                                    'backgroundColor': '#4CAF50',
                                    'color': 'white',
                                    'border': 'none',
                                    'borderRadius': '5px',
                                    'cursor': 'pointer'
                                }
                            ),
                            dcc.Download(id='download-dataframe-csv')
                        ], style={'textAlign': 'right'})
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
        df['Order creation date'] = pd.to_datetime(df['Order creation date'])
        
        # Convert numeric columns, removing any currency symbols
        numeric_columns = [
            'eBay collected tax', 'Item price', 'Quantity', 'Item subtotal',
            'Shipping and handling', 'Seller collected tax', 'Discount',
            'Gross amount', 'Final Value Fee - fixed', 'Final Value Fee - variable',
            'Below standard performance fee', 'Very high "item not as described" fee',
            'International fee', 'Deposit processing fee', 'Regulatory operating fee',
            'Promoted Listing Standard fee', 'Charity donation', 'Shipping labels',
            'Payment Dispute Fee', 'Expenses', 'Refunds', 'Order earnings'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), 
                    errors='coerce'
                ).fillna(0)  # Replace NaN with 0 for numeric columns
        
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
        
        # Fill NaN values appropriately
        df['Order number'] = df['Order number'].fillna('--')
        df['Item ID'] = df['Item ID'].fillna('--')
        df['Buyer name'] = df['Buyer name'].fillna('--')
        df['Ship to city'] = df['Ship to city'].fillna('--')
        df['Ship to province/region/state'] = df['Ship to province/region/state'].fillna('--')
        df['Ship to zip'] = df['Ship to zip'].fillna('--')
        df['Ship to country'] = df['Ship to country'].fillna('--')
        df['Transaction currency'] = df['Transaction currency'].fillna('--')
        df['Payout currency'] = df['Payout currency'].fillna('--')
        
        # Calculate any additional columns if needed
        fee_columns = [
            'Final Value Fee - fixed', 'Final Value Fee - variable',
            'Below standard performance fee', 'Very high "item not as described" fee',
            'International fee', 'Deposit processing fee', 'Regulatory operating fee',
            'Promoted Listing Standard fee'
        ]
        
        df['Total Fees'] = df[fee_columns].sum(axis=1)
        
        # Format the date column for CSV export
        df['Order creation date'] = df['Order creation date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
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
        df['Order creation date'] = pd.to_datetime(df['Order creation date'])
        df['month_year'] = df['Order creation date'].dt.strftime('%B %Y')
        month_year_options = sorted(
            [{'label': my, 'value': my} for my in df['month_year'].unique()],
            key=lambda x: pd.to_datetime(x['value'], format='%B %Y')
        )
        
        # Store the data as a JSON string
        data = df.to_json(date_format='iso', orient='split')
        start_date = df['Order creation date'].min()
        end_date = df['Order creation date'].max()
        
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
        current_theme = 'light'
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
    df['Order creation date'] = pd.to_datetime(df['Order creation date'])
    
    # Date filtering
    if start_date and end_date:
        df = df[
            (df['Order creation date'] >= start_date) & 
            (df['Order creation date'] <= end_date)
        ]
    
    # Month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Order creation date'].dt.month == month_year_date.month) &
            (df['Order creation date'].dt.year == month_year_date.year)
        ]
    
    # Feature filtering
    df = df[selected_features]
    
    # Format date column
    if 'Order creation date' in df.columns:
        df['Order creation date'] = df['Order creation date'].dt.strftime('%Y-%m-%d')
    
    # Format numeric columns
    numeric_columns = [
        'eBay collected tax', 'Item price', 'Quantity', 'Item subtotal',
        'Shipping and handling', 'Seller collected tax', 'Discount',
        'Gross amount', 'Final Value Fee - fixed', 'Final Value Fee - variable',
        'Below standard performance fee', 'Very high "item not as described" fee',
        'International fee', 'Deposit processing fee', 'Regulatory operating fee',
        'Promoted Listing Standard fee', 'Charity donation', 'Shipping labels',
        'Payment Dispute Fee', 'Expenses', 'Refunds', 'Order earnings'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].round(2)
    
    columns = [{'name': i, 'id': i} for i in df.columns]
    return df.to_dict('records'), columns

# Callback for Export
@app.callback(
    Output('download-dataframe-csv', 'data'),
    Input('export-button', 'n_clicks'),
    State('stored-data', 'data'),
    prevent_initial_call=True
)
def export_processed_data(n_clicks, stored_data):
    if not stored_data:
        return None
    
    # Load the processed data
    df = pd.read_json(stored_data, orient='split')
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Return the processed data as CSV
    return dcc.send_data_frame(
        df.to_csv,
        f'ebay_processed_data_{timestamp}.csv',
        index=False
    )

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
    df['Order creation date'] = pd.to_datetime(df['Order creation date'])
    
    # Apply date filtering
    if start_date and end_date:
        df = df[
            (df['Order creation date'] >= start_date) & 
            (df['Order creation date'] <= end_date)
        ]
    
    # Apply month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Order creation date'].dt.month == month_year_date.month) &
            (df['Order creation date'].dt.year == month_year_date.year)
        ]
    
    # Apply table filtering
    if filtered_rows and filtered_indices:
        df = pd.DataFrame(filtered_rows)
        if 'Order creation date' in df.columns:
            df['Order creation date'] = pd.to_datetime(df['Order creation date'])
        for col in df.columns:
            if col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    stats = []
    
    # Financial Statistics
    if all(col in selected_features for col in ['Gross amount', 'Order earnings']):
        # Calculate the total fees - only include columns that exist in the dataframe
        fee_columns = [
            'Final Value Fee - fixed', 'Final Value Fee - variable',
            'Below standard performance fee', 'Very high "item not as described" fee',
            'International fee', 'Deposit processing fee', 'Regulatory operating fee',
            'Promoted Listing Standard fee'
        ]
        available_fee_columns = [col for col in fee_columns if col in df.columns]
        total_fees = df[available_fee_columns].sum().sum() if available_fee_columns else 0
        
        total_gross = df['Gross amount'].sum()
        total_earnings = df['Order earnings'].sum()
        
        stats.extend([
            html.Div([
                html.H5('Gross Sales'),
                html.H3(f'${total_gross:,.2f}'),
                html.P('Before fees & expenses')
            ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center'}),
            
            html.Div([
                html.H5('Total Fees'),
                html.H3(f'${total_fees:,.2f}'),
                html.P('All eBay fees')
            ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center'}),
            
            html.Div([
                html.H5('Net Earnings'),
                html.H3(f'${total_earnings:,.2f}'),
                html.P('After all deductions')
            ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center'})
        ])
        
        # Only show fee rate if gross amount is positive
        if total_gross > 0:
            stats.append(
                html.Div([
                    html.H5('Fee Rate'),
                    html.H3(f'{(total_fees/total_gross*100):,.1f}%'),
                    html.P('of gross sales')
                ], style={'width': '25%', 'display': 'inline-block', 'textAlign': 'center'})
            )
    
    # Order Statistics
    if 'Order number' in selected_features:
        unique_orders = len(df[df['Order number'] != '--']['Order number'].unique())
        if unique_orders > 0 and 'Gross amount' in selected_features:
            avg_order_value = df[df['Order number'] != '--']['Gross amount'].sum() / unique_orders
            stats.extend([
                html.Div([
                    html.H5('Order Metrics'),
                    html.H3(f'{unique_orders:,}'),
                    html.P(f'Avg Value: ${avg_order_value:,.2f}')
                ], style={'width': '33%', 'display': 'inline-block', 'textAlign': 'center'})
            ])
    
    # Time Period Statistics
    if 'Order creation date' in selected_features:
        date_range = (df['Order creation date'].max() - df['Order creation date'].min()).days
        if 'Gross amount' in selected_features:
            daily_avg_sales = df['Gross amount'].sum() / (date_range + 1) if date_range >= 0 else df['Gross amount'].sum()
            
            stats.extend([
                html.Div([
                    html.H5('Time Period'),
                    html.H3(f'{date_range + 1} days'),
                    html.P(f'${daily_avg_sales:,.2f}/day')
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
    if stored_data is None or 'Order creation date' not in selected_features or 'Gross amount' not in selected_features:
        return go.Figure()
    
    # Load and process data
    df = pd.read_json(stored_data, orient='split')
    df['Order creation date'] = pd.to_datetime(df['Order creation date'])
    
    # Apply date filtering
    if start_date and end_date:
        df = df[
            (df['Order creation date'] >= start_date) & 
            (df['Order creation date'] <= end_date)
        ]
    
    # Apply month-year filtering
    if selected_month_year:
        month_year_date = pd.to_datetime(selected_month_year, format='%B %Y')
        df = df[
            (df['Order creation date'].dt.month == month_year_date.month) &
            (df['Order creation date'].dt.year == month_year_date.year)
        ]
    
    # Apply table filtering
    if filtered_rows and filtered_indices:
        df = pd.DataFrame(filtered_rows)
        df['Order creation date'] = pd.to_datetime(df['Order creation date'])
        for col in ['Gross amount', 'Order earnings']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Group by date and calculate daily amounts
    daily_data = df.groupby('Order creation date').agg({
        'Gross amount': 'sum',
        'Order earnings': 'sum' if 'Order earnings' in selected_features else 'sum'
    }).reset_index()
    
    # Set theme-specific colors
    theme_colors = DARK_THEME if theme == 'dark' else LIGHT_THEME
    
    # Create the figure
    fig = go.Figure()
    
    # Add the bar chart for gross amount
    fig.add_trace(go.Bar(
        x=daily_data['Order creation date'],
        y=daily_data['Gross amount'],
        name='Gross Sales',
        marker_color=theme_colors['accent']
    ))
    
    # Add the line for earnings if selected
    if 'Order earnings' in selected_features:
        fig.add_trace(go.Scatter(
            x=daily_data['Order creation date'],
            y=daily_data['Order earnings'],
            mode='lines',
            name='Net Earnings',
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
            title='Amount ($)',
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