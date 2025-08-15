# src/api/bot_dashboard.py
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import datetime
import asyncio

from src.trading.bot import TradingBot
from src.database.mongo import MongoDB

app = dash.Dash(__name__, use_async=True)
server = app.server  # For deployment

bot = TradingBot()
db = MongoDB()

AVAILABLE_PAIRS = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT']
AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
AVAILABLE_STRATEGIES = ['Mean Reversion', 'Momentum', 'Arbitrage']

app.layout = html.Div([
    html.H2("Trading Bot Control Dashboard"),

    html.Div([
        html.Button("Start Bot", id="start-button", n_clicks=0),
        html.Button("Stop Bot", id="stop-button", n_clicks=0),
        html.Span(id="bot-status", style={'marginLeft': '20px', 'fontWeight': 'bold'})
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
    ], style={'width':'45%', 'display':'inline-block', 'marginLeft':'5%'}),

    html.Div([
        html.Label(html.B("Select Strategy")),
        dcc.Dropdown(
            id='strategy-dropdown',
            options=[{'label': s, 'value': s} for s in AVAILABLE_STRATEGIES],
            value=AVAILABLE_STRATEGIES[0],
            clearable=False
        ),
        dcc.RadioItems(
            id='strategy-mode',
            options=[
                {'label': 'Manual', 'value': 'manual'},
                {'label': 'Auto', 'value': 'auto'}
            ],
            value='manual',
            labelStyle={'display': 'inline-block', 'marginRight': '15px'}
        ),
    ], style={'width':'45%', 'marginTop':'10px'}),

    html.Div([
        html.Label(html.B("Trading Mode")),
        dcc.RadioItems(
            id='trade-mode',
            options=[
                {'label': 'Paper Trade', 'value': 'paper'},
                {'label': 'Real Trade', 'value': 'real'}
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
            'height': '150px', 'overflowY': 'scroll', 'border': '1px solid #ccc',
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

    dcc.Interval(id='interval-update', interval=10*1000, n_intervals=0)  # 10 seconds interval
])

@app.callback(
    Output('pair-dropdown', 'value'),
    Input('all-pairs-check', 'value')
)
def update_pairs_checkbox(all_checked):
    if 'ALL' in all_checked:
        return AVAILABLE_PAIRS
    return []

@app.callback(
    Output("bot-status", "children"),
    [Input("start-button", "n_clicks"), Input("stop-button", "n_clicks")]
)
async def handle_bot_control(start_clicks, stop_clicks):
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered == "start-button":
        if not bot.running:
            last_settings = await db.db.settings.find_one({})
            if last_settings:
                bot.pairs = last_settings.get('pairs', [])
                bot.timeframes = last_settings.get('timeframes', [])
                bot.strategy = last_settings.get('strategy', AVAILABLE_STRATEGIES[0])
                bot.strategy_mode = last_settings.get('strategy_mode', 'manual')
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
    prevent_initial_call=True
)
async def save_settings_and_update_bot(n_clicks, pairs, timeframes, strategy, strategy_mode, trade_mode):
    if not pairs or not timeframes or not strategy or not strategy_mode or not trade_mode:
        return "Fill all settings before applying."

    settings_doc = {
        "pairs": pairs,
        "timeframes": timeframes,
        "strategy": strategy,
        "strategy_mode": strategy_mode,
        "trade_mode": trade_mode,
        "last_updated": datetime.datetime.utcnow()
    }
    await db.db.settings.replace_one({}, settings_doc, upsert=True)

    bot.pairs = pairs
    bot.timeframes = timeframes
    bot.strategy = strategy
    bot.strategy_mode = strategy_mode
    bot.trade_mode = trade_mode

    return "Settings saved and bot updated."

@app.callback(
    Output("current-trades-log", "children"),
    Output("trade-log-textarea", "value"),
    Input('interval-update', 'n_intervals')
)
async def update_trade_logs(n):
    trades = await db.get_trades()
    trades_text = "\n".join([str(t) for t in trades[-10:]])
    trade_logs_text = "\n".join([str(t) for t in trades[-50:]])
    return trades_text, trade_logs_text

@app.callback(
    Output("candlestick-chart", "figure"),
    Input("pair-dropdown", "value"),
    Input("timeframe-dropdown", "value"),
)
def update_chart(pairs, timeframes):
    if not pairs or not timeframes:
        return dash.no_update

    now = datetime.datetime.utcnow()
    times = [now - datetime.timedelta(minutes=i) for i in range(30)][::-1]

    opens = np.random.rand(30)*100 + 1000
    closes = opens + (np.random.rand(30)*10 - 5)
    highs = np.maximum(opens, closes) + np.random.rand(30)*5
    lows = np.minimum(opens, closes) - np.random.rand(30)*5

    df = pd.DataFrame({
        'Date': times,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes
    })

    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name=pairs[0]
    )])
    fig.update_layout(title=f'Candlestick: {pairs[0]} @ {timeframes[0]}',
                      xaxis_rangeslider_visible=False)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
