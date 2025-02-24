from dash import Dash, html, dcc, dash_table, Input, Output, State
import pandas as pd
import sqlite3
import io
import base64
import re
import numpy as np
import dash_bootstrap_components as dbc

# Initialize the Dash app
app = Dash(__name__)

# Global variables to maintain state
class DataStore:
    def __init__(self):
        self.df = pd.DataFrame()
        # Create a persisted in-memory SQLite database
        self.db_path = 'file::memory:?cache=shared'
        self._connection = None
        self.columns = []
        self.original_columns = {}  # Store mapping of original to cleaned names

    def get_connection(self):
        """Get or create a connection to the shared in-memory database"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path, 
                uri=True,
                check_same_thread=False
            )
        return self._connection

    def create_table(self, df):
        """Create the data table with the provided DataFrame"""
        conn = self.get_connection()
        df.to_sql('data', conn, index=False, if_exists='replace')

data_store = DataStore()

def clean_column_name(column):
    """Clean a column name to make it SQL-friendly and readable"""
    # Convert to lowercase
    name = str(column).lower()
    
    # Remove special characters and extra spaces
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    # Split on spaces and get meaningful words
    words = name.split()
    
    # Remove common filler words
    filler_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    words = [w for w in words if w not in filler_words]
    
    # If no words left after cleaning, return 'column'
    if not words:
        return 'column'
    
    # Join remaining words
    name = '_'.join(words)
    
    # Ensure name starts with a letter
    if not name[0].isalpha():
        name = 'col_' + name
    
    return name

def clean_column_names(df):
    """Clean all column names in the DataFrame and return mapping"""
    original_names = {}
    new_names = []
    
    for col in df.columns:
        clean_name = clean_column_name(col)
        
        # Handle duplicate cleaned names
        base_name = clean_name
        counter = 1
        while clean_name in new_names:
            clean_name = f"{base_name}_{counter}"
            counter += 1
        
        new_names.append(clean_name)
        original_names[clean_name] = col
    
    # Rename columns in DataFrame
    df.columns = new_names
    return df, original_names

def format_scalar_value(value):
    """Format scalar values for display"""
    if isinstance(value, (np.float64, float)):
        return f"{value:,.2f}"
    elif isinstance(value, (np.int64, int)):
        return f"{value:,}"
    return str(value)

def is_scalar_result(df):
    """Check if the result is a scalar (single value)"""
    return len(df) == 1 and len(df.columns) == 1

def is_single_row_result(df):
    """Check if the result is a single row with multiple columns"""
    return len(df) == 1 and len(df.columns) > 1

def create_result_component(result_df):
    """Create appropriate component based on query result type"""
    if result_df.empty:
        return html.Div("Query returned no results", className="text-gray-600 italic")
    
    elif is_scalar_result(result_df):
        # Handle scalar result
        value = result_df.iloc[0, 0]
        return html.Div([
            html.P("Query Result:", className="font-semibold mb-2"),
            html.Div(
                format_scalar_value(value),
                className="text-2xl font-bold text-blue-600 p-4 bg-blue-50 rounded"
            )
        ])
    
    elif is_single_row_result(result_df):
        # Handle single row with multiple columns
        return html.Div([
            html.P("Query Results:", className="font-semibold mb-2"),
            html.Div(
                [
                    html.Div([
                        html.Span(col, className="font-medium text-gray-600"),
                        html.Span(": "),
                        html.Span(format_scalar_value(result_df.iloc[0][col]), 
                                className="font-bold text-blue-600")
                    ], className="mb-2")
                    for col in result_df.columns
                ],
                className="p-4 bg-blue-50 rounded"
            )
        ])
    
    else:
        # Return regular DataTable for tabular results
        return dash_table.DataTable(
            id='results-table',
            columns=[{"name": i, "id": i} for i in result_df.columns],
            data=result_df.to_dict('records'),
            page_size=200,
            style_table={'overflowX': 'auto'},
            style_cell={
                'padding': '10px',
                'textAlign': 'left'
            },
            style_header={
                'backgroundColor': 'rgb(240, 240, 240)',
                'fontWeight': 'bold'
            }
        )

def validate_csv(contents, filename, max_size_mb=10):
    """Validate CSV file contents and return DataFrame if valid"""
    try:
        # Check file extension
        if not filename.lower().endswith('.csv'):
            return None, None, "Please upload a CSV file"
        
        # Check file size
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_size_mb = len(decoded) / (1024 * 1024)  # Convert to MB
        
        if file_size_mb > max_size_mb:
            return None, None, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
        
        # Decode and read file contents
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        
        # Validation checks
        if df.empty:
            return None, None, "The CSV file is empty"
        
        # Check for unlabeled columns
        unnamed_cols = df.columns.str.contains('^Unnamed:', na=False).any()
        if unnamed_cols:
            return None, None, "CSV must have labeled columns"
        
        # Clean column names
        df, original_names = clean_column_names(df)
        
        # Generate column mapping message
        # mapping_message = "Column names have been cleaned:\n" + \
        #                  "\n".join([f"'{k}' (was: '{v}')" for k, v in original_names.items()])
        mapping_message = ''
        
        return df, original_names, f"File uploaded successfully! \n\n{mapping_message}"
        
    except Exception as e:
        return None, None, f"Error processing file: {str(e)}"

# App layout
app.layout = html.Div([
    # Header
    html.H1('CSV SQL Explorer', 
            className='text-2xl font-bold mb-6'),
    
    # File Upload Section
    html.Div([
        html.H2('1. Upload Data', 
                className='text-xl font-semibold mb-3'),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select a CSV File', 
                      className='underline text-blue-600')
            ]),
            className='border-2 border-dashed p-6 text-center rounded-lg hover:bg-gray-50',
            multiple=False
        ),
        html.Div(id='upload-status', 
                 className='mt-3 text-sm whitespace-pre-line')
    ], className='mb-8'),
    
    # Query Section
    html.Div([
        html.H2('2. Query Data', 
                className='text-xl font-semibold mb-3'),
        
        # Column information
        html.Div([
            html.Strong('Available Columns:', 
                       className='block mb-2'),
            html.Div(id='column-list', 
                    className='text-sm bg-gray-100 p-3 rounded')
        ], className='mb-4'),
        
        # Query examples
        html.Div([
            html.Strong('Example Queries:', className='block mb-2'),
            html.Div([
                html.Code('SELECT * FROM data LIMIT 5', className='block'),
                html.Code('SELECT COUNT(*) FROM data', className='block'),
                html.Code('SELECT ship_province_region_state, COUNT(item_title) FROM data GROUP BY ship_province_region_state ORDER BY COUNT(item_title) DESC', className='block'),
            ], className='text-sm bg-gray-100 p-3 rounded font-mono')
        ], className='mb-4'),
        
        # Query input
        html.Div([
            html.Label('Enter SQL Query:', 
                      className='block mb-2 font-medium'),
            dcc.Textarea(
                id='sql-query',
                placeholder='SELECT * FROM data',
                className='w-full p-3 border rounded shadow-sm',
                style={'height': 100}
            ),
            html.Button(
                'Run Query',
                id='run-query',
                className='mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700'
            )
        ], className='mb-4'),
        
        # Error display
        html.Div(id='query-error', 
                 className='text-red-600 text-sm mb-4'),
        
        # Results section
        html.Div([
            html.Div(id='results-info', 
                    className='text-sm text-gray-600 mb-2'),
            html.Div(id='query-results-container', 
                    className='mt-4')
        ])
    ], id='query-section', style={'display': 'none'})
], className='container mx-auto px-4 py-8 max-w-6xl')

# Callback for file upload
@app.callback(
    [Output('query-section', 'style'),
     Output('upload-status', 'children'),
     Output('upload-status', 'className'),
     Output('column-list', 'children'),
     Output('sql-query', 'value'),
     Output('query-results-container', 'children'),
     Output('results-info', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def process_upload(contents, filename):
    if contents is None:
        return {'display': 'none'}, '', '', '', '', None, ''
    
    # Validate and process the uploaded file
    df, original_names, message = validate_csv(contents, filename)
    
    if df is None:
        return (
            {'display': 'none'},
            message,
            'mt-3 text-sm text-red-600',
            '',
            '',
            None,
            ''
        )
    
    # Update global data store
    data_store.df = df
    data_store.create_table(df)  # Create the table in the shared database
    data_store.columns = df.columns.tolist()
    data_store.original_columns = original_names
    
    return (
        {'display': 'block'},
        message,
        'mt-3 text-sm text-green-600',
        ', '.join(df.columns),
        'SELECT * FROM data LIMIT 5',
        create_result_component(df.head()),
        f'Showing first 5 rows of {len(df)} total rows'
    )

# Callback for query execution
@app.callback(
    [Output('query-results-container', 'children', allow_duplicate=True),
     Output('query-error', 'children'),
     Output('results-info', 'children', allow_duplicate=True)],
    Input('run-query', 'n_clicks'),
    State('sql-query', 'value'),
    prevent_initial_call=True
)
def run_query(n_clicks, query):
    if not query:
        return dash.no_update, '', dash.no_update
    
    try:
        # Use the shared connection
        conn = data_store.get_connection()
        # Execute query and get results
        result_df = pd.read_sql_query(query, conn)
        
        # Create appropriate result component
        result_component = create_result_component(result_df)
        
        # Generate appropriate info message
        if is_scalar_result(result_df):
            info_message = "Query returned a single value"
        elif is_single_row_result(result_df):
            info_message = "Query returned a single row"
        else:
            info_message = f"Query returned {len(result_df)} rows"
        
        return result_component, '', info_message
        
    except Exception as e:
        return (
            create_result_component(data_store.df.head()),
            f'Query error: {str(e)}',
            f'Showing first 5 rows of {len(data_store.df)} total rows'
        )

# Add Tailwind CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>CSV SQL Explorer</title>
        {%favicon%}
        {%css%}
        <script src="https://cdn.tailwindcss.com"></script>
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