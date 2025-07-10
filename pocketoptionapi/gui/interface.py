"""Simplified GUI for visualizing predictions and patterns."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..ml import MultiSymbolPatternDetector


@dataclass
class TradingGUI:
    """Basic Tkinter GUI for multi-symbol pattern detection visualization."""

    symbols: Iterable[str]
    detector: Optional[MultiSymbolPatternDetector] = None

    def __post_init__(self) -> None:
        self.symbols = list(self.symbols)
        if self.detector is None:
            self.detector = MultiSymbolPatternDetector(symbols=self.symbols)
        self.root = tk.Tk()
        self.root.title("Trading Pattern Visualizer")
        self.create_widgets()
        self.data: Dict[str, pd.DataFrame] = {}

    def create_widgets(self) -> None:
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.load_button = tk.Button(control_frame, text="Load CSV", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT)

        self.run_button = tk.Button(control_frame, text="Run Prediction", command=self.run_prediction)
        self.run_button.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(control_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)

        self.figure = Figure(figsize=(8, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_csv(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            self.status_var.set(f"Failed to load CSV: {exc}")
            return
        if "symbol" not in df.columns or "price" not in df.columns or "time" not in df.columns:
            self.status_var.set("CSV must contain symbol, time, price columns")
            return
        for sym in df["symbol"].unique():
            self.data[sym] = df[df["symbol"] == sym].copy()
        self.status_var.set("Data loaded")
        self.plot_data()

    def plot_data(self, predictions: Optional[Dict[str, List[float]]] = None) -> None:
        self.ax.clear()
        for sym, df in self.data.items():
            self.ax.plot(df["time"], df["price"], label=f"{sym} price")
            if predictions and sym in predictions:
                self.ax.plot(df["time"], predictions[sym], "--", label=f"{sym} predicted")
        self.ax.legend()
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Price")
        self.figure.tight_layout()
        self.canvas.draw()

    def run_prediction(self) -> None:
        if not self.data:
            self.status_var.set("Load data first")
            return
        self.status_var.set("Predicting...")
        self.root.update()
        predictions: Dict[str, List[float]] = {}
        for sym, df in self.data.items():
            preds: List[float] = []
            for _, row in df.iterrows():
                result = self.detector.process_tick(sym, row.to_dict())
                pred = result.get("prediction")
                preds.append(pred if pred is not None else row["price"])
            predictions[sym] = preds
        self.status_var.set("Prediction complete")
        self.plot_data(predictions)

    def run(self) -> None:
        self.root.mainloop()
