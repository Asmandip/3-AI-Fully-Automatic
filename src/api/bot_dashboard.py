# src/api/bot_dashboard.py
import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import asyncio
from src.trading.bot import TradingBot

app = dash.Dash(__name__)
bot = TradingBot()

# Sample pairs and timeframes
AVAILABLE_PAIRS = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT']
AVAILABLE_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

app.layout = html.Div([
    html.H2("Trading Bot Dashboard"),
    
    html.Div([
        html.Button("Start Bot", id='start-button', n_clicks=0),
        html.Button("Stop Bot", id='stop-button', n_clicks=0),
        html.Div(id='bot-status', style={'marginLeft': '20px', 'display': 'inline-block'})
    ], style={'marginBottom': '20px'}),

    html.Div([
        html.Label("Select Trading Pairs:"),
        dcc.Dropdown(
            id='pair-dropdown',
            options=[{'label': px, 'value': px} for px in AVAILABLE_PAIRS],
            value=['BTC/USDT'],
            multi=True
        )
    ], style={'width':'40%', 'display':'inline-block', 'marginRight':'20px'}),
    
    html.Div([
        html.Label("Select Timeframes:"),
        dcc.Dropdown(
            id='timeframe-dropdown',
            options=[{'label': tf, 'value': tf} for tf in AVAILABLE_TIMEFRAMES],
            value=['1m'],
            multi=True
        )
    ], style={'width':'40%', 'display':'inline-block'}),

    html.Br(),
    html.Button("Apply Settings", id='apply-settings-btn', n_clicks=0),
    html.Div(id='apply-settings-msg', style={'color': 'green', 'marginTop': '10px'}),

    html.Hr(),

    html.Div([
        html.H4("Current Trades"),
        html.Div(id='current-trades', style={'whiteSpace': 'pre-wrap', 'fontFamily': 'monospace', 'border':'1px solid #ccc', 'padding': '10px', 'height': '150px', 'overflowY': 'scroll'})
    ], style={'marginTop': '20px'}),

    html.Div([
        html.H4("Trade Log"),
        dcc.Textarea(
            id='trade-log',
            style={'width':'100%', 'height':'200px', 'fontFamily': 'monospace'},
            readOnly=True
        )
    ], style={'marginTop': '20px'}),

    html.Div([
        html.H4("Candlestick Chart"),
        dcc.Graph(id='candlestick-chart')
    ], style={'marginTop': '20px'}),

    dcc.Interval(
        id='update-interval',
        interval=10000,  # 10 sec
        n_intervals=0
    )
])

# Dummy in-memory storages for trade log and current trades
trade_log_storage = []
current_trades_storage = []

@app.callback(
    Output('bot-status', 'children'),
    [Input('start-button', 'n_clicks'),
     Input('stop-button', 'n_clicks')]
)
def control_bot(start_clicks, stop_clicks):
    changed_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if changed_id == 'start-button' and start_clicks > 0:
        if not bot.running:
            asyncio.create_task(bot.run())
        return "Bot Status: Running"
    elif changed_id == 'stop-button' and stop_clicks > 0:
        bot.stop()
        return "Bot Status: Stopped"
    else:
        return "Bot Status: " + ("Running" if bot.running else "Stopped")

@app.callback(
    Output('apply-settings-msg', 'children'),
    Input('apply-settings-btn', 'n_clicks'),
    State('pair-dropdown', 'value'),
    State('timeframe-dropdown', 'value')
)
def apply_settings(n_clicks, pairs, timeframes):
    if n_clicks > 0:
        # Save settings to DB or config (Pseudo code)
        # await save_settings_to_db(pairs, timeframes)
        return f"Settings applied. Pairs: {pairs}, Timeframes: {timeframes}"
    return ""

@app.callback(
    Output('current-trades', 'children'),
    Output('trade-log', 'value'),
    Input('update-interval', 'n_intervals')
)
def update_trades(n):
    # Refresh trade logs and current trade data
    trades_display = "\n".join([f"{t}" for t in current_trades_storage[-10:]])
    trade_logs = "\n".join(trade_log_storage[-50:])
    return trades_display, trade_logs

@app.callback(
    Output('candlestick-chart', 'figure'),
    Input('pair-dropdown', 'value'),
    Input('timeframe-dropdown', 'value')
)
def update_candlestick(pairs, timeframes):
    # Just plot dummy candlestick chart for first pair/timeframe combo
    # Replace with real OHLCV data fetching and plot
    if not pairs or not timeframes:
        return {}
    
    import pandas as pd
    import plotly.graph_objs as go
    import datetime

    now = datetime.datetime.now()
    # Dummy data
    df = pd.DataFrame({
        'Date': [now - datetime.timedelta(minutes=5*i) for i in range(10)][::-1],
        'Open': [100+i for i in range(10)],
        'High': [101+i for i in range(10)],
        'Low': [99+i for i in range(10)],
        'Close': [100+i+((i%2)*2-1) for i in range(10)],
    })

    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close']
    )])
    fig.update_layout(title=f'Candlestick Chart: {pairs[0]} / {timeframes[0]}',
                      xaxis_rangeslider_visible=False)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
