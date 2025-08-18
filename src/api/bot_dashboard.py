import dash
from dash_extensions.enrich import DashProxy, Output, Input, State, html, dcc, callback
import plotly.graph_objs as go
import pandas as pd
import datetime
import ccxt
import logging
import os
import asyncio
import requests
from dash import callback_context
from src.utils.logger import get_logger
from src.database.mongo import MongoDB

# Initialize logger
logger = get_logger("Dashboard")

# Setup Dash app
from patch_dash import PatchedDashProxy

app = PatchedDashProxy(__name__, prevent_initial_callbacks=True)
server = app.server

# Initialize database
db = MongoDB()

# Configuration
BASE_API_URL = os.getenv("BASE_API_URL", "http://localhost:8000")
AVAILABLE_TIMEFRAMES = ['1m', '3m', '5m', '15m', '1h', '4h', '1d']
AVAILABLE_STRATEGIES = ['Mean Reversion', 'Momentum', 'Scalping']


# Fetch Bitget futures pairs
def fetch_bitget_futures_pairs():
    try:
        bitget = ccxt.bitget()
        markets = bitget.load_markets()
        pairs = [m for m in markets if '/USDT' in m and markets[m].get('type') == 'swap']
        return sorted(pairs)[:100]  # Limit to top 100 pairs
    except Exception as e:
        logger.error(f"Error fetching pairs: {e}")
        return []


AVAILABLE_PAIRS = fetch_bitget_futures_pairs()

# Layout
app.layout = html.Div([
    html.H1("Trading Bot Dashboard", style={'textAlign': 'center'}),

    # Bot Control Section
    html.Div([
        html.Button("Start Bot", id="start-button", className="btn btn-success"),
        html.Button("Stop Bot", id="stop-button", className="btn btn-danger", style={'marginLeft': '10px'}),
        html.Span(id="bot-status", className="badge bg-primary", style={'marginLeft': '20px', 'fontSize': '1.2em'}),
    ], className="card p-3 mb-4"),

    # Configuration Section
    html.Div([
        html.H4("Configuration", className="card-title"),

        html.Div([
            html.Div([
                html.Label("Select Trading Pairs", className="form-label"),
                dcc.Checklist(
                    id='all-pairs-check',
                    options=[{'label': 'Select All', 'value': 'ALL'}],
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
            ], className="col-md-5"),

            html.Div([
                html.Label("Select Timeframes", className="form-label"),
                dcc.Dropdown(
                    id='timeframe-dropdown',
                    options=[{'label': tf, 'value': tf} for tf in AVAILABLE_TIMEFRAMES],
                    value=['5m'],
                    multi=True,
                    placeholder="Select timeframe(s)"
                ),
            ], className="col-md-5"),
        ], className="row mb-3"),

        html.Div([
            html.Div([
                html.Label("Select Strategy", className="form-label"),
                dcc.Dropdown(
                    id='strategy-dropdown',
                    options=[{'label': s, 'value': s} for s in AVAILABLE_STRATEGIES],
                    value='Scalping',
                    clearable=False,
                ),
            ], className="col-md-3"),

            html.Div([
                html.Label("Strategy Mode", className="form-label"),
                dcc.RadioItems(
                    id='strategy-mode',
                    options=[
                        {'label': 'Manual', 'value': 'manual'},
                        {'label': 'Auto', 'value': 'auto'}
                    ],
                    value='auto',
                    inline=True
                ),
            ], className="col-md-3"),

            html.Div([
                html.Label("Trade Mode", className="form-label"),
                dcc.RadioItems(
                    id='trade-mode',
                    options=[
                        {'label': 'Paper', 'value': 'paper'},
                        {'label': 'Live', 'value': 'live'}
                    ],
                    value='paper',
                    inline=True
                ),
            ], className="col-md-3"),

            html.Div([
                html.Label("Trade Size (% of balance)", className="form-label"),
                dcc.Slider(
                    id='trade-size-slider',
                    min=0.1,
                    max=5,
                    step=0.1,
                    value=1,
                    marks={i: f"{i}%" for i in range(0, 6)},
                ),
            ], className="col-md-3"),
        ], className="row mb-3"),

        html.Div([
            html.Button("Apply Settings", id="apply-settings", className="btn btn-primary"),
            html.Div(id="apply-message", className="text-success mt-2"),
        ]),
    ], className="card p-3 mb-4"),

    # Monitoring Section
    html.Div([
        html.Div([
            html.H4("Active Trades", className="card-title"),
            html.Pre(id="current-trades-log", className="bg-light p-3 rounded",
                    style={'height': '200px', 'overflowY': 'auto'}),
        ], className="col-md-6"),

        html.Div([
            html.H4("Trade History", className="card-title"),
            html.Pre(id="trade-log-textarea", className="bg-light p-3 rounded",
                    style={'height': '200px', 'overflowY': 'auto'}),
        ], className="col-md-6"),
    ], className="row mb-4"),

    # Chart Section
    html.Div([
        html.H4("Market Data", className="card-title"),
        dcc.Dropdown(
            id='chart-pair-selector',
            options=[{'label': p, 'value': p} for p in AVAILABLE_PAIRS],
            value=AVAILABLE_PAIRS[0] if AVAILABLE_PAIRS else '',
            className="mb-3"
        ),
        dcc.Graph(id="candlestick-chart", style={'height': '500px'}),
    ], className="card p-3"),

    dcc.Interval(id='interval-update', interval=15 * 1000, n_intervals=0),
    dcc.Store(id='last-update', data=0),
], className="container mt-4")


# Callbacks
@callback(
    Output('pair-dropdown', 'value'),
    Input('all-pairs-check', 'value')
)
def update_pairs_checkbox(all_checked):
    return AVAILABLE_PAIRS if 'ALL' in all_checked else []


@callback(
    Output("bot-status", "children"),
    Input('interval-update', 'n_intervals')
)
def update_bot_status(n):
    try:
        response = requests.get(f"{BASE_API_URL}/health")
        if response.ok:
            status = response.json()
            return f"Status: {'Running' if status['bot_running'] else 'Stopped'}"
    except:
        pass
    return "Status: Unknown"


@callback(
    Output("apply-message", "children"),
    Input("apply-settings", "n_clicks"),
    State("pair-dropdown", "value"),
    State("timeframe-dropdown", "value"),
    State("strategy-dropdown", "value"),
    State("strategy-mode", "value"),
    State("trade-mode", "value"),
    State("trade-size-slider", "value"),
    prevent_initial_call=True
)
def save_settings(n_clicks, pairs, timeframes, strategy, strategy_mode, trade_mode, trade_size):
    if not pairs or not timeframes:
        return "Please select at least one pair and timeframe"

    settings = {
        "pairs": pairs,
        "timeframes": timeframes,
        "strategy": strategy,
        "strategy_mode": strategy_mode,
        "trade_mode": trade_mode,
        "trade_size": trade_size / 100,  # Convert percentage to decimal
        "last_updated": datetime.datetime.utcnow()
    }

    try:
        asyncio.run(db.save_settings(settings))
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return "Error saving settings"

    return f"Settings saved! Trading {len(pairs)} pairs on {len(timeframes)} timeframes"


@callback(
    Output("current-trades-log", "children"),
    Output("trade-log-textarea", "children"),
    Input('interval-update', 'n_intervals')
)
async def update_trade_logs(n):
    try:
        trades = await db.get_trades(limit=20)
        if not trades:
            return "No recent trades", "No trade history"

        current_trades = [t for t in trades if t.get('status') == 'open']
        trade_text = "\n".join([
            f"{t['timestamp'].strftime('%Y-%m-%d %H:%M')} | {t['pair']} | "
            f"{t['side'].upper()} | ${t.get('amount', 0):.2f} | "
            f"Profit: ${t.get('profit', 0):.2f}"
            for t in trades
        ])

        current_text = "No active trades" if not current_trades else "\n".join([
            f"{t['pair']} | {t['side'].upper()} | ${t.get('amount', 0):.2f} "
            f"@{t.get('price', 'N/A')} | Open: {t['timestamp'].strftime('%H:%M')}"
            for t in current_trades
        ])

        return current_text, trade_text
    except Exception as e:
        logger.error(f"Error updating logs: {e}")
        return "Error loading trades", "Error loading trade history"


@callback(
    Output("candlestick-chart", "figure"),
    Input("chart-pair-selector", "value"),
    Input("timeframe-dropdown", "value")
)
async def update_chart(pair, timeframes):
    if not pair or not timeframes:
        return go.Figure()

    try:
        from src.utils.data_fetcher import AsyncDataFetcher
        fetcher = AsyncDataFetcher()
        data = await fetcher.fetch_historical_data(pair, timeframes[0], 100)

        if not data:
            return go.Figure()

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=pair
        )])

        fig.update_layout(
            title=f'{pair} Price Chart ({timeframes[0]})',
            xaxis_title='Time',
            yaxis_title='Price',
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )

        return fig
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return go.Figure()


@callback(
    Output("bot-status", "children"),
    Input("start-button", "n_clicks"),
    Input("stop-button", "n_clicks"),
    prevent_initial_call=True
)
def control_bot(start, stop):
    ctx = callback_context
    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        if button_id == "start-button":
            requests.post(f"{BASE_API_URL}/start")
            return "Status: Running"
        elif button_id == "stop-button":
            requests.post(f"{BASE_API_URL}/stop")
            return "Status: Stopped"
    except Exception as e:
        logger.error(f"Control error: {e}")

    return ""


if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)