# src/api/bot_dashboard.py
import dash
from dash_extensions.enrich import Output, Input, State, html, dcc, callback
import datetime
import os
import asyncio
import requests
from threading import Thread
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

# Reuse HTTP session to reduce latency on periodic health checks
_http_session = requests.Session()

# Fetch Bitget futures pairs lazily to avoid blocking startup
AVAILABLE_PAIRS = []
def fetch_bitget_futures_pairs():
    try:
        # Import locally to avoid heavy import at startup
        import ccxt
        bitget = ccxt.bitget()
        markets = bitget.load_markets()
        pairs = [m for m in markets if '/USDT' in m and markets[m].get('type') == 'swap']
        return sorted(pairs)[:100]  # Limit to top 100 pairs
    except Exception as e:
        logger.error(f"Error fetching pairs: {e}")
        return []

# Layout
app.layout = html.Div([
    html.H1("ট্রেডিং বট ড্যাশবোর্ড", style={'textAlign': 'center'}),
    
    # Bot Control Section
    html.Div([
        html.Button("বট চালু করুন", id="start-button", className="btn btn-success"),
        html.Button("বট বন্ধ করুন", id="stop-button", className="btn btn-danger", style={'marginLeft': '10px'}),
        html.Span(id="bot-status", className="badge bg-primary", style={'marginLeft': '20px', 'fontSize': '1.2em'}),
    ], className="card p-3 mb-4"),
    
    # Configuration Section
    html.Div([
        html.H4("কনফিগারেশন", className="card-title"),
        
        html.Div([
            html.Div([
                html.Label("ট্রেডিং পেয়ার নির্বাচন করুন", className="form-label"),
                dcc.Checklist(
                    id='all-pairs-check',
                    options=[{'label': 'সব নির্বাচন করুন', 'value': 'ALL'}],
                    value=[],
                    labelStyle={'display': 'inline-block', 'marginRight': '10px'}
                ),
                dcc.Dropdown(
                    id='pair-dropdown',
                    options=[{'label': pair, 'value': pair} for pair in AVAILABLE_PAIRS],
                    value=[],
                    multi=True,
                    placeholder="পেয়ার নির্বাচন করুন"
                ),
            ], className="col-md-5"),
            
            html.Div([
                html.Label("টাইমফ্রেম নির্বাচন করুন", className="form-label"),
                dcc.Dropdown(
                    id='timeframe-dropdown',
                    options=[{'label': tf, 'value': tf} for tf in AVAILABLE_TIMEFRAMES],
                    value=['5m'],
                    multi=True,
                    placeholder="টাইমফ্রেম নির্বাচন করুন"
                ),
            ], className="col-md-5"),
        ], className="row mb-3"),
        
        html.Div([
            html.Div([
                html.Label("API Key", className="form-label"),
                dcc.Input(id='api-key-input', type='password'),
            ], className="col-md-3"),
            
            html.Div([
                html.Label("API Secret", className="form-label"),
                dcc.Input(id='api-secret-input', type='password'),
            ], className="col-md-3"),
            
            html.Div([
                html.Label("ট্রেডিং স্ট্র্যাটেজি", className="form-label"),
                dcc.Dropdown(
                    id='strategy-dropdown',
                    options=[{'label': s, 'value': s} for s in AVAILABLE_STRATEGIES],
                    value='Scalping',
                    clearable=False,
                ),
            ], className="col-md-3"),
            
            html.Div([
                html.Label("স্ট্র্যাটেজি মোড", className="form-label"),
                dcc.RadioItems(
                    id='strategy-mode',
                    options=[
                        {'label': 'ম্যানুয়াল', 'value': 'manual'},
                        {'label': 'অটো', 'value': 'auto'}
                    ],
                    value='auto',
                    inline=True
                ),
            ], className="col-md-3"),
        ], className="row mb-3"),
        
        html.Div([
            html.Div([
                html.Label("ট্রেড মোড", className="form-label"),
                dcc.RadioItems(
                    id='trade-mode',
                    options=[
                        {'label': 'পেপার ট্রেডিং', 'value': 'paper'},
                        {'label': 'লাইভ ট্রেডিং', 'value': 'live'}
                    ],
                    value='paper',
                    inline=True
                ),
            ], className="col-md-3"),
            
            html.Div([
                html.Label("ট্রেড সাইজ (ব্যালান্সের %)", className="form-label"),
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
            html.Button("সেটিংস প্রয়োগ করুন", id="apply-settings", className="btn btn-primary"),
            html.Div(id="apply-message", className="text-success mt-2"),
        ]),
    ], className="card p-3 mb-4"),
    
    # Monitoring Section
    html.Div([
        html.Div([
            html.H4("একটিভ ট্রেডসমূহ", className="card-title"),
            html.Pre(id="current-trades-log", className="bg-light p-3 rounded", 
                    style={'height': '200px', 'overflowY': 'auto'}),
        ], className="col-md-6"),
        
        html.Div([
            html.H4("ট্রেড হিস্টোরি", className="card-title"),
            html.Pre(id="trade-log-textarea", className="bg-light p-3 rounded", 
                    style={'height': '200px', 'overflowY': 'auto'}),
        ], className="col-md-6"),
    ], className="row mb-4"),
    
    # Chart Section
    html.Div([
        html.H4("মার্কেট ডেটা", className="card-title"),
        dcc.Dropdown(
            id='chart-pair-selector',
            options=[],
            value='',
            className="mb-3"
        ),
        dcc.Graph(id="candlestick-chart", style={'height': '500px'}),
    ], className="card p-3"),
    
    dcc.Interval(id='interval-update', interval=15*1000, n_intervals=0),
    dcc.Store(id='last-update', data=0),
    # Hidden div to satisfy callbacks without rendering
    html.Div(id="dummy-output", style={'display': 'none'})
], className="container mt-4")

# Callbacks
@callback(
    Output('pair-dropdown', 'value'),
    Input('all-pairs-check', 'value')
)
def update_pairs_checkbox(all_checked):
    if all_checked and 'ALL' in all_checked:
        return AVAILABLE_PAIRS
    return []

@callback(
    Output('pair-dropdown', 'options'),
    Output('chart-pair-selector', 'options'),
    Output('chart-pair-selector', 'value'),
    Input('interval-update', 'n_intervals')
)
def ensure_pairs_loaded(n):
    global AVAILABLE_PAIRS
    try:
        if not AVAILABLE_PAIRS:
            AVAILABLE_PAIRS = fetch_bitget_futures_pairs()
        options = [{'label': p, 'value': p} for p in AVAILABLE_PAIRS]
        value = AVAILABLE_PAIRS[0] if AVAILABLE_PAIRS else ''
        return options, options, value
    except Exception as e:
        logger.error(f"Failed to load pairs: {e}")
        return [], [], ''

@callback(
    Output("bot-status", "children"),
    Input('interval-update', 'n_intervals')
)
def update_bot_status(n):
    try:
        response = _http_session.get(f"{BASE_API_URL}/health", timeout=5)
        if response.ok:
            status = response.json()
            return f"স্ট্যাটাস: {'চলছে' if status['bot_running'] else 'বন্ধ'}"
    except:
        pass
    return "স্ট্যাটাস: অজানা"

@callback(
    Output("apply-message", "children"),
    Input("apply-settings", "n_clicks"),
    State("pair-dropdown", "value"),
    State("timeframe-dropdown", "value"),
    State("strategy-dropdown", "value"),
    State("strategy-mode", "value"),
    State("trade-mode", "value"),
    State("trade-size-slider", "value"),
    State("api-key-input", "value"),
    State("api-secret-input", "value"),
    prevent_initial_call=True
)
def save_settings(n_clicks, pairs, timeframes, strategy, strategy_mode, trade_mode, trade_size, api_key, api_secret):
    if not pairs or not timeframes:
        return "অনুগ্রহ করে অন্তত একটি পেয়ার এবং টাইমফ্রেম নির্বাচন করুন"
    
    settings = {
        "pairs": pairs,
        "timeframes": timeframes,
        "strategy": strategy,
        "strategy_mode": strategy_mode,
        "trade_mode": trade_mode,
        "trade_size": trade_size / 100,
        "api_key": api_key,
        "api_secret": api_secret,
        "last_updated": datetime.datetime.utcnow()
    }
    
    # Save to database in a thread
    def save_to_db():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(db.save_settings(settings))
        loop.close()
    
    Thread(target=save_to_db).start()
    return f"সেটিংস সংরক্ষিত! {len(pairs)} টি পেয়ারে {len(timeframes)} টি টাইমফ্রেমে ট্রেডিং"

@callback(
    Output("current-trades-log", "children"),
    Output("trade-log-textarea", "children"),
    Input('interval-update', 'n_intervals')
)
def update_trade_logs(n):
    try:
        trades = asyncio.run(db.get_trades(limit=20))
        if not trades:
            return "কোন একটিভ ট্রেড নেই", "কোন ট্রেড হিস্টোরি নেই"

        current_trades = [t for t in trades if t.get('status') == 'open']
        trade_text = "\n".join([
            f"{t['timestamp'].strftime('%Y-%m-%d %H:%M')} | {t['pair']} | "
            f"{t['side'].upper()} | ${t.get('amount', 0):.2f} | "
            f"লাভ: ${t.get('profit', 0):.2f}"
            for t in trades
        ])

        current_text = "কোন একটিভ ট্রেড নেই" if not current_trades else "\n".join([
            f"{t['pair']} | {t['side'].upper()} | ${t.get('amount', 0):.2f} "
            f"@{t.get('price', 'N/A')} | সময়: {t['timestamp'].strftime('%H:%M')}"
            for t in current_trades
        ])

        return current_text, trade_text
    except Exception as e:
        logger.error(f"লগ আপডেটে ত্রুটি: {e}")
        return "ট্রেড লোড করতে সমস্যা", "ট্রেড হিস্টোরি লোড করতে সমস্যা"

@callback(
    Output("candlestick-chart", "figure"),
    Input("chart-pair-selector", "value"),
    Input("timeframe-dropdown", "value")
)
def update_chart(pair, timeframes):
    # Import heavy libs lazily to speed up startup
    import pandas as pd
    import plotly.graph_objs as go
    if not pair or not timeframes:
        return go.Figure()

    try:
        # Fetch historical data lazily
        from src.trading.data_fetcher import AsyncDataFetcher
        fetcher = AsyncDataFetcher()
        data = asyncio.run(fetcher.fetch_historical_data(pair, timeframes[0], 100))

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
            title=f'{pair} প্রাইস চার্ট ({timeframes[0]})',
            xaxis_title='সময়',
            yaxis_title='দাম',
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )

        return fig
    except Exception as e:
        # Ensure failure does not break UI
        logger.error(f"চার্টে ত্রুটি: {e}")
        return go.Figure()
    finally:
        try:
            # Close underlying exchange connection
            from src.trading.data_fetcher import AsyncDataFetcher as _ADF  # noqa
            asyncio.run(fetcher.close())
        except Exception:
            pass

@callback(
    Output("dummy-output", "children"), 
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
            _http_session.post(f"{BASE_API_URL}/start", timeout=5)
        elif button_id == "stop-button":
            _http_session.post(f"{BASE_API_URL}/stop", timeout=5)
    except Exception as e:
        logger.error(f"কন্ট্রোল ত্রুটি: {e}")
    
    return ""

if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port=8050)