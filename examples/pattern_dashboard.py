"""Example Dash app for visualising pattern detection results."""

import random
from datetime import datetime

import dash
from dash import dcc, html
import plotly.graph_objs as go

from pocketoptionapi.ml.pattern_detector import MultiSymbolPatternDetector, TickData

app = dash.Dash(__name__)

detector = MultiSymbolPatternDetector(["EURUSD", "GBPUSD"])

def generate_tick(symbol: str) -> TickData:
    """Simulate tick data for demonstration purposes."""
    return TickData(timestamp=datetime.utcnow().timestamp(), price=random.uniform(1.0, 1.5))

app.layout = html.Div([
    dcc.Graph(id="price-chart"),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])

@app.callback(
    dash.dependencies.Output("price-chart", "figure"),
    [dash.dependencies.Input("interval", "n_intervals")]
)
def update_chart(n):
    tick = generate_tick("EURUSD")
    result = detector.add_tick("EURUSD", tick)
    prices = [t.price for t in detector.buffers["EURUSD"]]
    times = [datetime.fromtimestamp(t.timestamp) for t in detector.buffers["EURUSD"]]
    return {
        "data": [
            go.Scatter(x=times, y=prices, mode="lines", name="EURUSD"),
            go.Scatter(x=[times[-1]], y=[result["prediction"]], mode="markers", name="Prediction")
        ],
        "layout": go.Layout(title="EURUSD Price with Prediction")
    }

if __name__ == "__main__":
    app.run_server(debug=True)
