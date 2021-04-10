#!/usr/bin/env python
# coding: utf-8

from datetime import date, timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from utils import get_stock_dict
from controller import Controller, open_collapse

DATA_DIR = './Data/'
API_TOKEN = ""
FONT_DIR = './Font/SourceHanSansTW-Regular.otf'
VALID_USERNAME_PASSWORD_PAIRS = {
    'user': '88888888'
}

tw_dict, eng_dict = get_stock_dict()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )

# Get Data

@app.callback(
    Output('Header-Company', 'children'),
    Output('Company-ID', 'data'),
    Output('Crawler-Alert', 'is_open'),
    Output('Online-Alert', 'is_open'),
    Output('Error-Alert', 'is_open'),
    Output('Error-Alert', 'children'),
    [Input("Data-Mode", "value"), Input("Dropdown-Company", "value")]
)
def get_data(online_mode, company_id):
    global controller
    controller = Controller(DATA_DIR, FONT_DIR, company_id)
    return controller.get_data(eng_dict, API_TOKEN, online_mode)


@app.callback(
    Output('News-Table', 'children'),
    [Input('Company-ID', 'data')]
)
def update_news(company_id):
    controller.reset(company_id)
    return controller.update_news()


# Plot Price, Volume, Buy-Sell

@app.callback(
    Output('Price-Graph', 'figure'),
    Output('Header-TimeRange', 'children'),
    Output('Latest-Price', 'children'),
    Output('Latest-Updown', 'children'),
    Output('Latest-Price', 'style'),
    Output('Latest-Updown', 'style'),
    Output('Latest-Date', 'children'),
    [Input("Time-Slider", "start_date"),
     Input("Time-Slider", "end_date"),
     Input('Company-ID', 'data')]
)
def update_price_figure(start_date, end_date, company_id):
    controller.reset(company_id)
    return controller.update_price_figure(start_date, end_date)


# Plot Revenue YoY/MoM
@app.callback(
    Output('Revenue-Graph', 'figure'),
    Output('Revenue-Table', 'children'),
    Output('YoY-Label', 'children'),
    Output('MoM-Label', 'children'),
    [Input("Time-Slider", "start_date"),
     Input("Time-Slider", "end_date"), Input('Company-ID', 'data')]
)
def update_revenue_figure(start_date, end_date, company_id):
    controller.reset(company_id)
    return controller.update_revenue_figure(start_date, end_date)


@app.callback(
    Output('Financial-Statements-Graph', 'figure'),
    Output('Financial-Statements-Table', 'children'),
    Output('EPS-Label', 'children'),
    Output('Gross-Margin-Label', 'children'),
    [Input("Time-Slider", "start_date"), Input("Time-Slider", "end_date"),
     Input('Company-ID', 'data')]
)
def update_financial_statements_figure(start_date, end_date, company_id):
    controller.reset(company_id)
    return controller.update_financial_statements_figure(start_date, end_date)


@app.callback(
    Output('PE-Ratio-Label', 'children'),
    Output('PB-Ratio-Label', 'children'),
    [Input('Company-ID', 'data')]
)
def update_per_ratio(company_id):
    controller.reset(company_id)
    return controller.update_per_ratio()


@app.callback(
    Output('Shareholding-Graph', 'figure'),
    [Input("Time-Slider", "start_date"), Input("Time-Slider", "end_date"),
     Input('Company-ID', 'data')]
)
def update_shareholding(start_date, end_date, company_id):
    controller.reset(company_id)
    return controller.update_shareholding(start_date, end_date)


@app.callback(
    Output('News-Graph', 'figure'), Output("NLP-Button", "n_clicks"),
    [Input("NLP-Button", "n_clicks"), Input('Company-ID', 'data')]
)
def update_nlp_news(n, company_id):
    controller.reset(company_id)
    return controller.update_nlp_news(n)


@app.callback(
    Output("Revenue-Collapse", "is_open"),
    [Input("Revenue-Collapse-Button", "n_clicks")],
    [State("Revenue-Collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    return open_collapse(n, is_open)


@app.callback(
    Output("Financial-Statements-Collapse", "is_open"),
    [Input("Financial-Statements-Collapse-Button", "n_clicks")],
    [State("Financial-Statements-Collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    return open_collapse(n, is_open)


@app.callback(
    Output("News-Collapse", "is_open"),
    [Input("News-Collapse-Button", "n_clicks")],
    [State("News-Collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    return open_collapse(n, is_open)


######################################################################################
# View
######################################################################################
header_view = html.Div([
    dbc.Row(
        html.Br()),
    dbc.Row(
        dbc.Col(
            html.H3(
                id='Header-Company',
                children='Company Information',
                style={'textAlign': 'center'}))),
    dbc.Row(
        dbc.Col(
            html.H5(
                id='Header-TimeRange',
                children='From XXXX/X to XXXX/X',
                style={'textAlign': 'center'})))])

price_view = dbc.Col(
    dbc.FormGroup([
        dbc.Label("Price"),
        dbc.Spinner([html.H1(children='--', id='Latest-Price', style={'textAlign': 'center'}),
                     html.H6(children='--', id='Latest-Updown', style={'textAlign': 'center'})], size="sm"),
        dbc.Tooltip(
            children=" ",
            target="Latest-Price",
            id="Latest-Date"
        ),
    ]), width={"size": 2})

info_view = dbc.Card([
    dbc.Row([
        dbc.Col([
            html.H6("EPS:"),
            dbc.Spinner(
                html.H5(children='--', id='EPS-Label', style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                "每股盈餘 (EPS) = 本期稅後淨利 / 普通股在外流通股數",
                target="EPS-Label",
            ),
        ], width={"size": 1}),
        dbc.Col([
            html.H6("PER:"),
            dbc.Spinner(html.H5(children='--',
                                id='PE-Ratio-Label',
                                style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                "本益比 (倍) = 現在股價 (Price) / 預估未來每年每股盈餘 (EPS)",
                target="PE-Ratio-Label",
            ),
        ], width={"size": 1}),
        dbc.Col([
            html.H6("PBR:"),
            dbc.Spinner(html.H5(children='--', id='PB-Ratio-Label',
                                style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                ["股價淨值比(倍) = 現在股價 (Price) / 每股淨值",
                 html.Br(),
                 "淨值 = 資產總值 – 總負債和無形資產"],
                target="PB-Ratio-Label",
            ),
        ], width={"size": 1}),
        dbc.Col([
            html.H6("GPM:"),
            dbc.Spinner(html.H5(children='--', id='Gross-Margin-Label',
                                style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                "毛利率 = (銷售收入 - 銷售成本) / 銷售收入 × 100%",
                target="Gross-Margin-Label",
            ),
        ], width={"size": 1}),
        dbc.Col([
            html.H6("YoY:"),
            dbc.Spinner(
                html.H5(children='--', id='YoY-Label', style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                "營收年增率",
                target="YoY-Label",
            ),
        ], width={"size": 1}),
        dbc.Col([
            html.H6("MoM:"),
            dbc.Spinner(
                html.H5(children='--', id='MoM-Label', style={'textAlign': 'right'}), size="sm", type="grow"),
            dbc.Tooltip(
                "營收月增率",
                target="MoM-Label",
            ),
        ], width={"size": 1})
    ], justify="around")
], body=True)

graph_view = html.Div([
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.Tabs([
                    dbc.Tab([
                        dbc.Spinner(color="primary",
                                    children=dcc.Graph(id='Price-Graph'))], label="Price")
                ])
            ], body=True)
        ], md=7),
        dbc.Col([
            dbc.Card([
                dbc.Tabs([
                    dbc.Tab([
                        dbc.Spinner(color="primary",
                                    children=[dcc.Graph(id='Revenue-Graph')]),
                        html.Br(),
                        dbc.Button("Table",
                                   id="Revenue-Collapse-Button",
                                   className="mb-4",
                                   color="primary"),
                        dbc.Collapse(
                            dbc.Card(dbc.Table(id='Revenue-Table', style={'textAlign': 'right'}), body=True, style={
                                'height': 350, 'overflowY': 'auto'}), is_open=True, id='Revenue-Collapse')
                    ], label='Revenue'),

                    dbc.Tab([
                        dbc.Spinner(color="primary",
                                    children=[dcc.Graph(id='Financial-Statements-Graph')]),
                        html.Br(),
                        dbc.Button("Table",
                                   id="Financial-Statements-Collapse-Button",
                                   className="mb-4",
                                   color="primary"),
                        dbc.Collapse(dbc.Card(dbc.Table(id='Financial-Statements-Table', style={'textAlign': 'right'}),
                                              body=True, style={
                                'height': 350, 'overflowY': 'auto'}), is_open=True,
                                     id='Financial-Statements-Collapse'),
                    ], label='Income Statements'),

                    dbc.Tab([
                        dbc.Spinner(color="primary",
                                    children=[dcc.Graph(id='Shareholding-Graph')]),
                        html.Br(),
                    ], label='Shareholding'),

                    dbc.Tab([
                        html.Br(),
                        dbc.ButtonGroup(
                            [dbc.Button("NLP Analysis",
                                        id="NLP-Button",
                                        color="primary",
                                        n_clicks=0),
                             dbc.Button("Table",
                                        id="News-Collapse-Button",
                                        color="primary"),
                             ], className="mb-4"
                        ),
                        html.Br(),

                        dbc.Collapse(dbc.Card(dbc.Table(id='News-Table'),
                                              body=False, style={
                                'height': 400, 'overflowY': 'auto'}), is_open=True,
                                     id='News-Collapse'),

                        dbc.Spinner(color="primary",
                                    children=[dcc.Graph(id='News-Graph')]),

                    ], label='News'),

                ])
            ], body=True)
        ], md=5)],
        no_gutters=True, form=True),
])

######################################################################################
# Controller
######################################################################################

controller = dbc.Card([
    dbc.Row([
        dbc.Col(
            dbc.FormGroup([
                dbc.Label("Mode"),
                dbc.RadioItems(
                    id='Data-Mode',
                    options=[{'label': 'Online', 'value': True},
                             {'label': 'Offline', 'value': False}],
                    value=False,
                    inline=True)
            ]), width={"size": 1, "offset": 1}),

        dbc.Col(
            dbc.FormGroup([
                dbc.Label("Company"),
                dcc.Dropdown(
                    id='Dropdown-Company',
                    options=[
                        {'label': str(item) + ' ' + tw_dict[item], 'value': item} for item in tw_dict],
                    value=2330,
                    clearable=False)
            ]), width={"size": 2, "offset": 1}),

        dbc.Col(
            dbc.FormGroup([
                dbc.Label("Date"),
                html.Br(),
                dcc.DatePickerRange(
                    id='Time-Slider',
                    min_date_allowed=date(2012, 1, 1),
                    max_date_allowed=date.today(),
                    start_date=date.today() - timedelta(days=90),
                    end_date=date.today(),
                    display_format='YYYY.MM.DD',
                    minimum_nights=5)
            ]), width={"size": 3, "offset": 1}),

        price_view

    ])
], body=True)

######################################################################################
# Layout
######################################################################################
app.layout = dbc.Container([

    dcc.Store(id='Company-ID'),

    header_view,
    html.Hr(),
    controller,
    html.Br(),
    info_view,
    graph_view,
    html.Br(),
    dbc.Toast(children="The data is not in local, using Online Mode automatically.",
              icon="danger",
              header="Offline Mode Failed",
              id="Crawler-Alert",
              is_open=False,
              dismissable=True,
              style={"position": "fixed", "top": 20, "right": 10, "width": 350}),
    dbc.Toast(children="Get data from FinMind API Failed.",
              icon="danger",
              header="Read Data Failed",
              id="Error-Alert",
              is_open=False,
              dismissable=True,
              style={"position": "fixed", "top": 20, "right": 10, "width": 350}),
    dbc.Toast(children="Get data from FinMind API Success",
              icon="success",
              header="Online Mode",
              id="Online-Alert",
              is_open=False,
              dismissable=True,
              duration=10000,
              style={"position": "fixed", "top": 20, "right": 10, "width": 350}),
], fluid=True)

# Run app and display result inline in the notebook
if __name__ == '__main__':
    # app.run_server(host='140.112.26.18', port=7788, debug=False)
    app.run_server(debug=True)
