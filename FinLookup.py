#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import os
import plotly.graph_objs as go
from pandas.errors import EmptyDataError
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)


def check_dir(company_id, directory):
    for dirPath, dirNames, fileNames in os.walk(directory):
        if company_id not in dirNames:
            create_folder(directory + str(company_id))


def get_data_from_finmind(dataset, company_id, start_date, output_dir):
    url = "https://api.finmindtrade.com/api/v4/data"
    parameter = {
        "dataset": dataset,
        "data_id": str(company_id),
        "start_date": start_date,
        "token": API_TOKEN,
    }
    resp = requests.get(url, params=parameter)
    data = resp.json()
    data = pd.DataFrame(data["data"])
    data.to_csv(output_dir, index=False)


def toggle_switch(n, is_open):
    if n:
        return not is_open
    return is_open


DATA_DIR = './Data/'
API_TOKEN = ""

stock_table = pd.read_json('StockTable.json')
tw_dict = pd.Series(stock_table['公司簡稱'].values, stock_table['公司代號']).to_dict()
eng_dict = pd.Series(stock_table['英文簡稱'].values, stock_table['公司代號']).to_dict()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


# Get Data

@app.callback(
    Output('Header-Company', 'children'),
    Output('Company-ID', 'data'),
    Output('Crawler-Alert', 'is_open'),
    Output('Online-Alert', 'is_open'),
    [Input("Data-Mode", "value"), Input("Dropdown-Company", "value")]
)
def get_data(online_mode, company_id):
    company_id = str(company_id)
    check_dir(company_id, DATA_DIR)

    dir_ = DATA_DIR + company_id + "/"
    alert = False
    for dirPath, dirNames, fileNames in os.walk(dir_):
        if company_id + '_Price.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockPrice", company_id,
                                  "2009-01-01", dir_ + company_id + '_Price.csv')

        if company_id + '_Revenue.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockMonthRevenue", company_id,
                                  "2008-01-01", dir_ + company_id + '_Revenue.csv')

        if company_id + '_Investors_Buy_Sell.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockInstitutionalInvestorsBuySell", company_id,
                                  "2008-01-01", dir_ + company_id + '_Investors_Buy_Sell.csv')

        if company_id + '_PER.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockPER", company_id, (date.today(
            ) - timedelta(days=90)).isoformat(), dir_ + company_id + '_PER.csv')

        if company_id + '_Financial_Statements.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockFinancialStatements", company_id,
                                  "2008-01-01", dir_ + company_id + '_Financial_Statements.csv')

        if company_id + '_Margin_Trading.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockMarginPurchaseShortSale", company_id,
                                  "2008-01-01", dir_ + company_id + '_Margin_Trading.csv')

        if company_id + '_Shareholding.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockShareholding", company_id,
                                  "2008-01-01", dir_ + company_id + '_Shareholding.csv')

        if company_id + '_News.csv' not in fileNames or online_mode:
            alert = True
            get_data_from_finmind("TaiwanStockNews", company_id,
                                  (date.today() - timedelta(days=20)).isoformat(), dir_ + company_id + '_News.csv')

    if online_mode:
        alert = False

    return eng_dict[int(company_id)] + ' Information', company_id, alert, online_mode


@app.callback(
    Output('News-Table', 'children'),
    [Input('Company-ID', 'data')]
)
def update_news(company_id):
    dir_ = DATA_DIR + company_id + "/"
    try:
        data = pd.read_csv(dir_ + company_id + '_News.csv')
        data = data.sort_values(by=['date'], ascending=False)
        table = data[['date', 'title']].copy()
        table.columns = ['Date', 'Title']
    except EmptyDataError:
        table = pd.DataFrame(['No Data'], columns=['Status'])

    table = dbc.Table.from_dataframe(
        table, striped=True, bordered=False, hover=True, responsive=True)

    return table


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
    dir_ = DATA_DIR + company_id + "/"

    df_price = pd.read_csv(dir_ + company_id + '_Price.csv')
    df_price.index = pd.to_datetime(df_price['date'])

    df_investors_buy_sell = pd.read_csv(
        dir_ + company_id + '_Investors_Buy_Sell.csv')
    df_investors_buy_sell.index = pd.to_datetime(df_investors_buy_sell['date'])

    df_margin_trading = pd.read_csv(
        dir_ + company_id + '_Margin_Trading.csv')
    df_margin_trading.index = pd.to_datetime(df_margin_trading['date'])

    latest_price = df_price.iloc[-1].close
    latest_date = "Latest updated at " + str(df_price.iloc[-1].date)
    latest_up_down = df_price.iloc[-1].close - df_price.iloc[-2].close
    latest_percent = latest_up_down * 100 / df_price.iloc[-2].close

    if latest_up_down > 0:
        latest_up_down = '▲ ' + \
                         str(round(latest_up_down, 2)) + \
                         " (" + str(round(latest_percent, 2)) + "%)"
        latest_color = 'green'
    else:
        latest_up_down = '▼ ' + \
                         str(-round(latest_up_down, 2)) + \
                         " (" + str(-round(latest_percent, 2)) + "%)"
        latest_color = 'red'

    latest_style = {'textAlign': 'center', 'color': latest_color}

    filtered_df_price = df_price[(df_price.index >= start_date)
                                 & (df_price.index <= end_date)].copy()

    filtered_df_investors_buy_sell = df_investors_buy_sell[(df_investors_buy_sell.index >= start_date)
                                                           & (df_investors_buy_sell.index <= end_date)].copy()

    filtered_df_margin_trading = df_margin_trading[(df_margin_trading.index >= start_date) & (
            df_margin_trading.index <= end_date)].copy()

    filtered_df_investors_buy_sell.insert(
        2, "Net", filtered_df_investors_buy_sell.buy - filtered_df_investors_buy_sell.sell, True)
    filtered_df_investors_buy_sell = filtered_df_investors_buy_sell.groupby(
        filtered_df_investors_buy_sell.index).sum()

    fig = make_subplots(rows=4, cols=1,
                        shared_xaxes=True,
                        row_heights=[0.8, 0.2, 0.2, 0.2],
                        vertical_spacing=0.08,
                        subplot_titles=("Price", "Volume",
                                        "Investors Buy & Sell", "Margin Trading & Short Selling")
                        )

    fig.add_trace(go.Bar(x=filtered_df_price.index,
                         y=filtered_df_price.Trading_Volume, name='Trading Volume'), row=2, col=1)
    fig.add_trace(go.Bar(x=filtered_df_investors_buy_sell.index,
                         y=filtered_df_investors_buy_sell.Net, name='Net Volume'), row=3, col=1)

    filtered_df_margin_trading.insert(2, "NetMarginTrading", filtered_df_margin_trading.MarginPurchaseBuy -
                                      filtered_df_margin_trading.MarginPurchaseSell -
                                      filtered_df_margin_trading.MarginPurchaseCashRepayment, True)

    filtered_df_margin_trading.insert(2, 'NetShortSelling', filtered_df_margin_trading.ShortSaleSell -
                                      filtered_df_margin_trading.ShortSaleBuy -
                                      filtered_df_margin_trading.ShortSaleCashRepayment, True)

    fig.add_trace(go.Bar(x=filtered_df_margin_trading.index,
                         y=filtered_df_margin_trading.NetMarginTrading, name='Margin Trading'), row=4, col=1)

    fig.add_trace(go.Bar(x=filtered_df_margin_trading.index,
                         y=filtered_df_margin_trading.NetShortSelling, name='Short Selling'), row=4, col=1)

    #         '''
    #     "MarginPurchaseBuy  融資買進"
    #     "MarginPurchaseSell  融資賣出"
    #     "MarginPurchaseTodayBalance  融資餘額"
    #     "ShortSaleBuy 融卷買進"
    #     "ShortSaleSell  融卷賣出"
    #     "ShortSaleTodayBalance 融卷餘額"
    #     '''

    max_buy_sell = max([abs(buy_sell)
                        for buy_sell in filtered_df_investors_buy_sell.Net])

    max_margin_short = max([abs(value)
                            for value in filtered_df_margin_trading.NetMarginTrading.append(
            filtered_df_margin_trading.NetShortSelling)])

    fig.update_yaxes(range=[-max_buy_sell * 1.1,
                            max_buy_sell * 1.1], row=3, col=1)

    fig.update_yaxes(range=[-max_margin_short * 1.1,
                            max_margin_short * 1.1], row=4, col=1)

    fig.add_trace(go.Candlestick(x=filtered_df_price.index,
                                 open=filtered_df_price['open'],
                                 high=filtered_df_price['max'],
                                 low=filtered_df_price['min'],
                                 close=filtered_df_price['close'],
                                 name='Price'), row=1, col=1)

    fig.update_xaxes(
        rangeslider_visible=False)

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), margin=dict(l=20, r=50, t=50, b=20), showlegend=False, height=900, hovermode='x unified')

    return fig, 'From ' + str(start_date) + ' to ' + str(end_date), str(round(latest_price, 2)), str(
        latest_up_down), latest_style, latest_style, latest_date


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
    dir_ = DATA_DIR + company_id + "/"

    df_revenue = pd.read_csv(dir_ + company_id + '_Revenue.csv')
    df_revenue.index = pd.to_datetime(df_revenue['date'])

    df_revenue['MoM'] = (df_revenue.revenue /
                         df_revenue.revenue.shift(1) - 1) * 100
    df_revenue['YoY'] = (df_revenue.revenue /
                         df_revenue.revenue.shift(12) - 1) * 100

    if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(days=365):
        filtered_df_revenue = df_revenue[
            (df_revenue.index >= start_date)
            & (df_revenue.index <= end_date)]
    else:
        filtered_df_revenue = df_revenue[
            (df_revenue.index >= datetime(year=datetime.strptime(
                end_date, "%Y-%m-%d").year - 1, month=1, day=1))
            & (df_revenue.index <= end_date)]

    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=("Revenue", "YoY & MoM")
                        )

    fig.add_trace(go.Bar(x=filtered_df_revenue.index,
                         y=filtered_df_revenue['revenue'], name='Month Revenue'), row=1, col=1)

    fig.add_trace(go.Scatter(x=filtered_df_revenue.index,
                             y=filtered_df_revenue['YoY'], mode="lines+markers", name='YoY'), row=2, col=1)
    fig.add_trace(go.Scatter(x=filtered_df_revenue.index,
                             y=filtered_df_revenue['MoM'], mode="lines+markers", name='MoM'), row=2, col=1)

    max_ratio = max([abs(ratio) for ratio in list(
        filtered_df_revenue['YoY']) + list(filtered_df_revenue['MoM'])])

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), margin=dict(l=20, r=50, t=50, b=50), showlegend=False, height=450, hovermode='x unified')

    fig.update_yaxes(range=[filtered_df_revenue['revenue'].min(
    ) * 0.9, filtered_df_revenue['revenue'].max() * 1.1], row=1, col=1)
    fig.update_yaxes(range=[-max_ratio * 1.1, max_ratio *
                            1.1], ticksuffix="%", row=2, col=1)

    table = filtered_df_revenue[['date', 'revenue', 'YoY', 'MoM']]

    table.loc[:, 'revenue'] = table['revenue'].to_numpy() / 1000000

    table.columns = ['Date', 'Revenue (M)', 'YoY (%)', 'MoM (%)']

    table = table.round({'Revenue (M)': 1, 'YoY (%)': 2, 'MoM (%)': 2})

    table = table.sort_values(by=['Date'], ascending=False)

    table = dbc.Table.from_dataframe(
        table, striped=True, bordered=False, hover=True, responsive=True)

    return fig, table, str(round(df_revenue['YoY'].iloc[-1], 1)) + '%', str(
        round(df_revenue['MoM'].iloc[-1], 1)) + '%'


@app.callback(
    Output('Financial-Statements-Graph', 'figure'),
    Output('Financial-Statements-Table', 'children'),
    Output('EPS-Label', 'children'),
    Output('Gross-Margin-Label', 'children'),
    [Input("Time-Slider", "start_date"), Input("Time-Slider", "end_date"),
     Input('Company-ID', 'data')]
)
def update_financial_statements_figure(start_date, end_date, company_id):
    dir_ = DATA_DIR + company_id + "/"

    df = pd.read_csv(dir_ + company_id + '_Financial_Statements.csv')
    df.index = pd.to_datetime(df['date'])

    latest_eps = df[df['type'] == 'EPS'].iloc[-1].value

    if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(days=5 * 365):
        filtered_df = df[(df.index >= start_date)
                         & (df.index <= end_date)]
    else:
        filtered_df = df[(df.index >= datetime(year=datetime.strptime(end_date, "%Y-%m-%d").year - 5, month=1, day=1))
                         & (df.index <= end_date)]

    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        subplot_titles=("EPS", "Gross Margin")
                        )
    gross_margin = filtered_df[filtered_df['type'] == 'GrossProfit'].value * 100 / filtered_df[
        filtered_df['type'] == 'Revenue'].value
    latest_gross_margin = gross_margin[-1]

    fig.add_trace(go.Scatter(x=filtered_df[filtered_df['type'] == 'EPS'].index,
                             y=filtered_df[filtered_df['type'] == 'EPS'].value, mode="lines+markers", name='EPS'),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=filtered_df[filtered_df['type'] == 'Revenue'].index,
                             y=gross_margin, mode="lines+markers", name='Gross Margin'), row=2, col=1)

    fig.update_yaxes(ticksuffix="%", row=2, col=1)

    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1), margin=dict(l=20, r=50, t=50, b=50), height=450, showlegend=False, hovermode='x unified')

    table = df[df['date'] == df.iloc[-1].date]

    value = []

    for row in table.iterrows():
        if row[1].type != 'EPS':
            value.append(row[1].value / 1000000)
        else:
            value.append(row[1].value)

    table.loc[:, 'value'] = value

    table.columns = ['Date', 'Stock Id', 'Type', 'Value (M)', df.iloc[-1].date]
    table = table[[df.iloc[-1].date, 'Value (M)']]

    table = dbc.Table.from_dataframe(
        table, striped=True, bordered=False, hover=True, responsive=True)

    return fig, table, str(latest_eps), str(round(latest_gross_margin, 1)) + "%"


@app.callback(
    Output('PE-Ratio-Label', 'children'),
    Output('PB-Ratio-Label', 'children'),
    [Input('Company-ID', 'data')]
)
def update_per_ratio(company_id):
    dir_ = DATA_DIR + company_id + "/"
    df = pd.read_csv(dir_ + company_id + '_PER.csv')
    return str(df.iloc[-1].PER), str(df.iloc[-1].PBR)


@app.callback(
    Output('Shareholding-Graph', 'figure'),
    [Input("Time-Slider", "start_date"), Input("Time-Slider", "end_date"),
     Input('Company-ID', 'data')]
)
def update_shareholding(start_date, end_date, company_id):
    dir_ = DATA_DIR + company_id + "/"

    df = pd.read_csv(dir_ + company_id + '_Shareholding.csv')
    df.index = pd.to_datetime(df['date'])

    if (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")) > timedelta(days=5 * 365):
        filtered_df = df[(df.index >= start_date)
                         & (df.index <= end_date)]
    else:
        filtered_df = df[(df.index >= datetime(year=datetime.strptime(end_date, "%Y-%m-%d").year - 5, month=1, day=1))
                         & (df.index <= end_date)]

    fig = make_subplots(subplot_titles=("Foreign Investors' Shareholding",))
    fig.add_trace(go.Scatter(x=filtered_df.index, y=100 * filtered_df.ForeignInvestmentShares /
                                                    filtered_df.NumberOfSharesIssued, name="Shares Held",
                             fill='tozeroy'))
    fig.add_trace(go.Scatter(x=filtered_df.index, y=100 * (filtered_df.ForeignInvestmentShares +
                                                           filtered_df.ForeignInvestmentRemainingShares) / filtered_df.NumberOfSharesIssued,
                             name="Upper Limit", fill='tonexty'))
    fig.add_trace(go.Scatter(x=filtered_df.index, y=100 * filtered_df.NumberOfSharesIssued /
                                                    filtered_df.NumberOfSharesIssued, name="Total"))

    fig.update_layout(margin=dict(l=20, r=50, t=50, b=50),
                      showlegend=False, height=450, hovermode='x unified')

    fig.update_yaxes(ticksuffix="%")

    return fig


@app.callback(
    Output("Revenue-Collapse", "is_open"),
    [Input("Revenue-Collapse-Button", "n_clicks")],
    [State("Revenue-Collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    return toggle_switch(n, is_open)


@app.callback(
    Output("Financial-Statements-Collapse", "is_open"),
    [Input("Financial-Statements-Collapse-Button", "n_clicks")],
    [State("Financial-Statements-Collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    return toggle_switch(n, is_open)


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
                                'height': 350, 'overflowY': 'scroll'}), is_open=True, id='Revenue-Collapse')
                    ], label='Monthly Revenue'),

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
                                'height': 350, 'overflowY': 'scroll'}), is_open=True,
                                     id='Financial-Statements-Collapse'),
                    ], label='Income Statements'),

                    dbc.Tab([
                        dbc.Spinner(color="primary",
                                    children=[dcc.Graph(id='Shareholding-Graph')]),
                        html.Br(),
                        # dbc.Button("Table",
                        #            id="Financial-Statements-Collapse-Button",
                        #            className="mb-4",
                        #            color="primary"),
                        # dbc.Collapse(dbc.Card(dbc.Table(id='Financial-Statements-Table', style={'textAlign': 'right'}),
                        #                       body=True, style={
                        #         'height': 350, 'overflowY': 'scroll'}), is_open=True,
                        #              id='Financial-Statements-Collapse'),
                    ], label='Shareholding'),

                    dbc.Tab([
                        html.Br(),
                        dbc.Card(dbc.Table(id='News-Table'), body=False,
                                 style={'height': 800, 'overflowY': 'scroll'})
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
    dbc.Toast("The data is not in local, using Online Mode automatically.",
              icon="danger",
              header="Offline Mode Failed",
              id="Crawler-Alert",
              is_open=False,
              dismissable=True,
              style={"position": "fixed", "top": 20, "right": 10, "width": 350}),
    dbc.Toast("Get data from FinMind API Success",
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
    # app.run_server(host='140.112.26.18', port=7788, debug=True)
    app.run_server(debug=True)
