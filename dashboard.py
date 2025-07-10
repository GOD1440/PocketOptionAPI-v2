import base64
import io

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

app = dash.Dash(__name__)

data_store = {}

instructions = """
### Instructions
1. Upload one or more CSV files containing historical data. Each file should have the columns `time`, `open`, `high`, `low`, `close`, `volume`, and `open_interest`.
2. Select the symbols to display from the dropdown.
3. Click **Run Prediction** to forecast future prices. Detected manipulation spikes will be highlighted.
"""

app.layout = html.Div([
    html.H1("Price Manipulation Detection Dashboard"),
    dcc.Markdown(instructions),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload CSV Files'),
        multiple=True
    ),
    dcc.Dropdown(id='symbol-select', multi=True, placeholder="Select symbols"),
    html.Button('Run Prediction', id='predict-btn'),
    dcc.Loading(dcc.Graph(id='price-chart')),
    html.Div(id='prediction-info')
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    df['time'] = pd.to_datetime(df['time'])
    df.sort_values('time', inplace=True)
    symbol = filename.split('.')[0]
    return symbol, df

@app.callback(
    Output('symbol-select', 'options'),
    Output('symbol-select', 'value'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        for c, n in zip(list_of_contents, list_of_names):
            sym, df = parse_contents(c, n)
            data_store[sym] = df
        options = [{'label': k, 'value': k} for k in data_store.keys()]
        return options, list(data_store.keys())
    raise dash.exceptions.PreventUpdate

@app.callback(
    Output('price-chart', 'figure'),
    Output('prediction-info', 'children'),
    Input('symbol-select', 'value'),
    Input('predict-btn', 'n_clicks')
)
def update_graph(symbols, n_clicks):
    if not symbols:
        return go.Figure(), ''

    fig = go.Figure()
    info_lines = []
    for sym in symbols:
        df = data_store.get(sym)
        if df is None:
            continue
        fig.add_trace(go.Candlestick(
            x=df['time'], open=df['open'], high=df['high'],
            low=df['low'], close=df['close'], name=f'{sym}'))
        fig.add_trace(go.Scatter(
            x=df['time'], y=df['volume'], name=f'{sym} Volume',
            yaxis='y2', mode='lines', line=dict(dash='dot')))
        if 'open_interest' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['time'], y=df['open_interest'], name=f'{sym} Open Interest',
                yaxis='y3', mode='lines', line=dict(dash='dash')))

        if n_clicks:
            pred, score = predict(df)
            pred_time = pd.date_range(df['time'].iloc[-1], periods=len(pred)+1, freq='1T')[1:]
            fig.add_trace(go.Scatter(x=pred_time, y=pred, mode='lines',
                                     name=f'{sym} Prediction'))
            info_lines.append(f"**{sym} R^2:** {score:.2f}")

        spikes = detect_manipulation(df)
        for t in spikes:
            fig.add_vline(x=t, line_color='red')

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        yaxis2=dict(overlaying='y', side='right', showgrid=False, title='Volume'),
        yaxis3=dict(overlaying='y', side='right', position=1.07, showgrid=False,
                     title='Open Interest'),
        legend=dict(x=0, y=1.1)
    )
    return fig, dcc.Markdown('\n'.join(info_lines))

def predict(df, steps=5):
    df = df.reset_index(drop=True)
    X = np.arange(len(df)).reshape(-1, 1)
    y = df['close'].values
    model = LinearRegression()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    future_X = np.arange(len(df), len(df) + steps).reshape(-1, 1)
    pred = model.predict(future_X)
    return pred, score

def detect_manipulation(df, threshold=3):
    returns = df['close'].pct_change().dropna()
    std = returns.std()
    spikes = df['time'][abs(returns) > threshold * std]
    return spikes

if __name__ == '__main__':
    app.run(debug=True)
