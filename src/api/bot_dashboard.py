# src/api/bot_dashboard.py
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import pandas as pd
import asyncio
import datetime

from src.trading.bot import TradingBot
from src.database.mongo import MongoDB

app = dash.Dash(__name__)
server = app.server

# Initialize Bot and Database
bot = TradingBot()
db = MongoDB()

# Available options
AVAILABLE_PAIRS = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT']
AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

# Layout Definition
app.layout = html.Div([
    html.H2("Trading Bot Control Dashboard"),

    html.Div([
        html.Button("Start Bot", id="start-button", n_clicks=0),
        html.Button("Stop Bot", id="stop-button", n_clicks=0),
        html.Span(id="bot-status", style={'marginLeft':'20px', 'fontWeight':'bold'})
    ], style={'marginBottom': '20px'}),

    html.Div([
        html.Label("Select Trading Pairs"),
        dcc.Dropdown(
            id='pair-dropdown',
            options=[{'label': pair, 'value': pair} for pair in AVAILABLE_PAIRS],
            value=[],
            multi=True,
            placeholder="Select one or more pairs"
        ),
    ], style={'width': '45%', 'display': 'inline-block'}),

    html.Div([
        html.Label("Select Timeframes"),
        dcc.Dropdown(
            id='timeframe-dropdown',
            options=[{'label': tf, 'value': tf} for tf in AVAILABLE_TIMEFRAMES],
            value=[],
            multi=True,
            placeholder="Select one or more timeframes"
        ),
    ], style={'width':'45%', 'display':'inline-block', 'marginLeft':'5%'}),

    html.Button("Apply Settings", id="apply-settings", n_clicks=0, style={'marginTop': '10px'}),
    html.Div(id="apply-message", style={"color": "green", "marginTop": "10px"}),

    html.Hr(),

    html.Div([
        html.H4("Current Trades"),
        html.Pre(id="current-trades-log", style={'height': '150px', 'overflowY': 'scroll', 'border': '1px solid #ccc', 'padding': '10px', 'fontFamily': 'monospace'})
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

    dcc.Interval(id='interval-update', interval=10*1000, n_intervals=0)  # Update every 10 seconds
])

# In-memory store for demonstration; replace with DB persistence retrieval
current_trades = []
trade_log = []

@app.callback(
    Output("bot-status", "children"),
    Input("start-button", "n_clicks"),
    Input("stop-button", "n_clicks"),
    prevent_initial_call=True,
)
def handle_bot_control(start_clicks, stop_clicks):
    triggered = callback_context.triggered[0]['prop_id'].split('.')
    if triggered == "start-button":
        if not bot.running:
            asyncio.create_task(bot.run())
        return "Bot Status: Running"
    elif triggered == "stop-button":
        if bot.running:
            bot.stop()
        return "Bot Status: Stopped"
    return "Bot Status: " + ("Running" if bot.running else "Stopped")

@app.callback(
    Output("apply-message", "children"),
    Input("apply-settings", "n_clicks"),
    State("pair-dropdown", "value"),
    State("timeframe-dropdown", "value"),
    prevent_initial_call=True,
)
def save_settings(n_clicks, pairs, timeframes):
    if not pairs or not timeframes:
        return "Please select at least one pair and one timeframe."
    # Save to DB asynchronously (simplified synchronous dummy here)
    # In production, call async function with event loop
    settings_doc = {
        "pairs": pairs,
        "timeframes": timeframes,
        "timestamp": datetime.datetime.utcnow()
    }
    asyncio.create_task(db.db.settings.replace_one({}, settings_doc, upsert=True))
    return f"Settings saved: {pairs} | {timeframes}"

@app.callback(
    Output("current-trades-log", "children"),
    Output("trade-log-textarea", "value"),
    Input('interval-update', 'n_intervals')
)
def update_trade_logs(n):
    # Fetch latest trade logs and current trades from DB (dummy here)
    # Replace these dummy storages with real DB queries for production
    trades_display = "\n".join(map(str, current_trades[-10:]))
    logs_display = "\n".join(trade_log[-50:])
    return trades_display, logs_display

@app.callback(
    Output("candlestick-chart", "figure"),
    Input("pair-dropdown", "value"),
    Input("timeframe-dropdown", "value"),
)
def update_chart(pairs, timeframes):
    import pandas as pd
    import numpy as np

    if not pairs or not timeframes:
        return dash.no_update

    # Dummy OHLCV data generation for first selected pair/timeframe
    now = datetime.datetime.utcnow()
    times = [now - datetime.timedelta(minutes=i*(1 if timeframes[0]=='1m' else 5)) for i in range(30)][::-1]

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
    fig.update_layout(title=f'Candlestick: {pairs} @ {timeframes}',
                      xaxis_rangeslider_visible=False)
    return fig

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)
