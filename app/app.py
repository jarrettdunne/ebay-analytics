from dash import Dash, Input, Output, State, callback, html, dcc, dash_table
import plotly.express as px 
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc


def transform(df):
    df.replace('--', np.nan, inplace=True)
    report = df[df['Type'] == 'Order']
    report = report[['Transaction creation date', 'Type', 'Order number', 'Net amount', 'Item title', 'Buyer username']]
    report.rename(columns={'Transaction creation date': 'date'}, inplace=True)
    report.rename(columns={'Type': 'type'}, inplace=True)
    report.rename(columns={'Order number': 'order'}, inplace=True)
    report.rename(columns={'Net amount': 'net'}, inplace=True)
    report.rename(columns={'Item title': 'title'}, inplace=True)
    report.rename(columns={'Buyer username': 'buyer'}, inplace=True)

    # print(report[report['Date'].str.contains('apr', case=False)])
    # report = report[~report['Date'].str.contains('apr', case=False)]

    orders = report[report['type'] == 'order']
    n, m = orders.shape
    ref = dict()
    for i in range(n):
        order = orders['order'].iloc[i]
        item = orders['title'].iloc[i]
        ref[order] = item

    n, m = report.shape
    for i in range(n):
        title = np.nan
        try:
            if report['title'].iloc[i] is np.nan:
                report['title'].iloc[i] = ref[report['order'].iloc[i]]
        except KeyError:
            print('key not found')
    return report

app = Dash(__name__)

df = pd.read_csv('reports/Transaction_report_20240101_20240913.csv', skiprows=[0,1,2,3,4,5,6,7,8,9,10])
print(df.head())
df = transform(df)
head = df.head()
fig = px.bar(df, x='date', y='net')


app.layout = dbc.Container([
    html.H1(children='ebay Dashboard'),
    html.Div(
        children=[
        dcc.Checklist(df.columns, id='labels-checklist', inline=True),
        ],
        style={'width': '49%', 'height': '100%'}
    ),
    html.Div(
        children=[
            dcc.Input(id='input-title'),
            dcc.Dropdown(
                style={'width': '100px'}
            ),
            dcc.Dropdown(
                style={'width': '100px'}
            ),
        ],
        style={'width': '49%', 'display': 'flex', 'height': '100%'},
    ),
    html.H1(id='input-output'),
    html.Div(
        children=[
        dash_table.DataTable(
            data=df.to_dict('records'), 
            columns=[{"name": i, "id": i} for i in df.columns], 
            id='tbl', 
            editable=True,
            cell_selectable=True
            ),
        html.Div(children=[dcc.Graph(figure=fig, id='example-graph')]),
        ],
        style={'width': '49%', 'display': 'flex'}
    ),
    # dbc.Alert(id='tbl_out'),
])

def search(df, column, term):
    return df[column]

def create_bar_chart(df, x_axis, y_axis):
    fig = px.bar(df, x=x_axis, y=y_axis)
    return fig

@callback(Output('input-output', 'children'), Input('input-title', 'value'))
def get_searched_table(value):
    return value

# @callback(Output(), Input())
# def update_bar_chart(value):
#     return

@callback(
        Output('tbl', 'children'),
        Input('labels-checklist', 'active_columns'),
)
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"

if __name__ == '__main__':
    app.run(debug=True)