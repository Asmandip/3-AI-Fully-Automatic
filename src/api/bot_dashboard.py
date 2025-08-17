# src/api/bot_dashboard.py

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import datetime
import ccxt
import asyncio
import logging

from src.trading.bot import TradingBot
from src.database.mongo import MongoDB

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("Dashboard")

app = dash.Dash(__name__)
server = app.server

bot = TradingBot()
db = MongoDB()


def fetch_bitget_futures_pairs():
    logger.debug("fetch_bitget_futures_pairs called")
    try:
        bitget = ccxt.bitget()
        markets = bitget.load_markets()
        pairs = (m for m in markets if '/USDT' in m and markets[m].get('type') == 'swap')
        pairs_list = list(pairs)[:100]
        logger.debug(f"Pairs fetched: {pairs_list[:5]}... total {len(pairs_list)}")
        del markets
        del pairs
        return sorted(pairs_list)
    except Exception as e:
        logger.error(f"Error fetching pairs: {e}")
        return []


AVAILABLE_PAIRS = fetch_bitget_futures_pairs()
AVAILABLE_TIMEFRAMES = ['1m', '3m', '5m', '15m', '1h', '4h', '1d']
AVAILABLE_STRATEGIES = ['Mean Reversion', 'Momentum', 'Arbitrage', 'Scalping']

app.layout = html.Div([
    html.H2("Trading Bot Control Dashboard"),

    html.Div([
        html.Button("Start Bot", id="start-button", n_clicks=0),
        html.Button("Stop Bot", id="stop-button", n_clicks=0),
        html.Span(id="bot-status", style={'marginLeft': '20px', 'fontWeight': 'bold'}),
    ], style={'marginBottom': '20px'}),

    html.Div([
        html.Label(html.B("Select Trading Pairs")),
        dcc.Checklist(
            id='all-pairs-check',
            options=[{'label': 'All Pairs', 'value': 'ALL'}],
            value=[],
            labelStyle={'display': 'inline-block', 'marginRight': '10px'}
        ),
        dcc.Dropdown(
            id='pair-dropdown',
            options=[{'label': pair, 'value': pair} for pair in AVAILABLE_PAIRS],
            value=[],
            multi=True,
            placeholder="Select pair(s)"
        ),
    ], style={'width': '45%', 'display': 'inline-block'}),

    html.Div([
        html.Label(html.B("Select Timeframes")),
        dcc.Dropdown(
            id='timeframe-dropdown',
            options=[{'label': tf, 'value': tf} for tf in AVAILABLE_TIMEFRAMES],
            value=['1m'],
            multi=True,
            placeholder="Select timeframe(s)"
        ),
    ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'}),

    html.Div([
        html.Label(html.B("Select Strategy")),
        dcc.Dropdown(
            id='strategy-dropdown',
            options=[{'label': s, 'value': s} for s in AVAILABLE_STRATEGIES],
            value='Scalping',
            clearable=False,
        ),
        dcc.RadioItems(
            id='strategy-mode',
            options=[
                {'label': 'Manual', 'value': 'manual'},
                {'label': 'Auto', 'value': 'auto'}
            ],
            value='auto'
        ),
    ], style={'width': '45%', 'marginTop': '10px'}),

    html.Div([
        html.Label(html.B("Trading Mode")),
        dcc.RadioItems(
            id='trade-mode',
            options=[
                {'label': 'Paper Trade', 'value': 'paper'},
                {'label': 'Live Trade', 'value': 'live'}
            ],
            value='paper',
            labelStyle={'display': 'inline-block', 'marginRight': '20px'}
        ),
    ], style={'marginTop': '10px'}),

    html.Button("Apply Settings", id="apply-settings", n_clicks=0, style={'marginTop': '15px'}),
    html.Div(id="apply-message", style={"color": "green", "marginTop": "10px"}),

    html.Hr(),

    html.Div([
        html.H4("Current Trades"),
        html.Pre(id="current-trades-log", style={
            'height': '150px', 'overflowY': 'auto', 'border': '1px solid #ccc',
            'padding': '10px', 'fontFamily': 'monospace'
        })
    ]),

    html.Div([
        html.H4("Trade Log"),
        dcc.Textarea(
            id='trade-log-textarea',
            style={'width': '100%', 'height': '200px', 'fontFamily': 'monospace'},
            readOnly=True,
            value=''
        )
    ]),

    html.Div([
        html.H4("Candlestick Chart"),
        dcc.Graph(id="candlestick-chart")
    ]),

    dcc.Interval(id='interval-update', interval=10*1000, n_intervals=0),
])


@app.callback(
    Output('pair-dropdown', 'value'),
    Input('all-pairs-check', 'value')
)
def update_pairs_checkbox(all_checked):
    logger.debug(f"update_pairs_checkbox called with: {all_checked}")
    if 'ALL' in all_checked:
        logger.debug("Selecting all pairs")
        return AVAILABLE_PAIRS
    logger.debug("All pairs not selected")
    return []


@app.callback(
    Output("bot-status", "children"),
    Input("start-button", "n_clicks"),
    Input("stop-button", "n_clicks"),
)
def handle_bot_control(start_clicks, stop_clicks):
    logger.debug(f"handle_bot_control called, start: {start_clicks}, stop: {stop_clicks}")
    triggered = callback_context.triggered[0]['prop_id'].split('.') if callback_context.triggered else None
    logger.debug(f"Triggered action: {triggered}")
    if triggered == "start-button":
        if not bot.running:
            last_settings = asyncio.run(db.get_settings())
            logger.debug(f"Last settings from DB: {last_settings}")
            if last_settings:
                bot.pairs = last_settings.get('pairs', [])
                bot.timeframes = last_settings.get('timeframes', [])
                bot.strategy = last_settings.get('strategy', 'Scalping')
                bot.strategy_mode = last_settings.get('strategy_mode', 'auto')
                bot.trade_mode = last_settings.get('trade_mode', 'paper')
            asyncio.create_task(bot.run())
        return "Status: Running"
    elif triggered == "stop-button":
        if bot.running:
            bot.stop()
        return "Status: Stopped"
    return "Status: Running" if bot.running else "Status: Stopped"


@app.callback(
    Output("apply-message", "children"),
    Input("apply-settings", "n_clicks"),
    State("pair-dropdown", "value"),
    State("timeframe-dropdown", "value"),
    State("strategy-dropdown", "value"),
    State("strategy-mode", "value"),
    State("trade-mode", "value"),
    prevent_initial_call=True,
)
def save_settings_and_update_bot(n_clicks, pairs, timeframes, strategy, strategy_mode, trade_mode):
    logger.debug(f"save_settings_and_update_bot called with pairs: {pairs}, timeframes: {timeframes}, strategy: {strategy}, strategy_mode: {strategy_mode}, trade_mode: {trade_mode}")
    if not pairs or not timeframes or not strategy or not strategy_mode or not trade_mode:
        logger.warning("Incomplete settings received")
        return "Fill all settings before applying."

    settings_doc = {
        "pairs": pairs,
        "timeframes": timeframes,
        "strategy": strategy,
        "strategy_mode": strategy_mode,
        "trade_mode": trade_mode,
        "last_updated": datetime.datetime.utcnow()
    }
    asyncio.run(db.save_settings(settings_doc))

    bot.pairs = pairs
    bot.timeframes = timeframes
    bot.strategy = strategy
    bot.strategy_mode = strategy_mode
    bot.trade_mode = trade_mode

    if trade_mode == "paper":
        bot.balance = 100.0

    logger.info(f"Settings saved and bot updated - trade mode: {trade_mode}")

    return f"Settings saved. Trade mode: {trade_mode}"


@app.callback(
    Output("current-trades-log", "children"),
    Output("trade-log-textarea", "value"),
    Input('interval-update', 'n_intervals'),
)
def update_trade_logs(n):
    logger.debug(f"update_trade_logs called - interval count {n}")
    trades = asyncio.run(db.get_trades())
    trades_text = "\n".join([str(t) for t in trades[-10:]])
    trade_logs_text = "\n".join([str(t) for t in trades[-50:]])
    return trades_text, trade_logs_text


@app.callback(
    Output("candlestick-chart", "figure"),
    Input("pair-dropdown", "value"),
    Input("timeframe-dropdown", "value"),
)
def update_chart(pairs, timeframes):
    logger.debug(f"update_chart called with pairs: {pairs}, timeframes: {timeframes}")
    if not pairs or not timeframes:
        logger.debug("No pairs or timeframes selected for chart update")
        return dash.no_update

    now = datetime.datetime.utcnow()
    times = (now - datetime.timedelta(minutes=i) for i in range(30))
    times = list(times)[::-1]

    opens = (1000 + np.random.random() * 100 for _ in range(30))
    closes = (o + (np.random.random() * 10 - 5) for o in opens)
    opens, closes = list(opens), list(closes)

    highs = (max(o, c) + np.random.random() * 5 for o, c in zip(opens, closes))
    lows = (min(o, c) - np.random.random() * 5 for o, c in zip(opens, closes))
    highs, lows = list(highs), list(lows)

    df = pd.DataFrame({
        "Date": times,
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
    })

    fig = go.Figure(data=[go.Candlestick(
        x=df["Date"], open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name=pairs[0]
    )])
    fig.update_layout(title=f'Candlestick: {pairs} @ {timeframes}', xaxis_rangeslider_visible=False)
    logger.debug("Chart figure updated")
    return fig


if __name__ == "__main__":
    logger.info("Starting Dash server")
    app.run_server(debug=True, host='0.0.0.0', port=8050)
