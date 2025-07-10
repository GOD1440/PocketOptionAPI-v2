"""Simplified GUI for visualizing predictions and patterns."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
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
        self.sym_vars: Dict[str, tk.IntVar] = {}

    def create_widgets(self) -> None:
        instruction = tk.Label(self.root, text="Load CSV then run prediction. Select symbols to display.")
        instruction.pack(side=tk.TOP, fill=tk.X)

        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.load_button = tk.Button(control_frame, text="Load CSV", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT)

        self.run_button = tk.Button(control_frame, text="Run Prediction", command=self.run_prediction)
        self.run_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(control_frame, length=150, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(control_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)

        self.symbol_frame = tk.Frame(self.root)
        self.symbol_frame.pack(side=tk.TOP, fill=tk.X)

        self.figure = Figure(figsize=(8, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        NavigationToolbar2Tk(self.canvas, self.root)

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
        for widget in self.symbol_frame.winfo_children():
            widget.destroy()
        self.sym_vars.clear()
        for sym in df["symbol"].unique():
            self.data[sym] = df[df["symbol"] == sym].copy()
            var = tk.IntVar(value=1)
            chk = tk.Checkbutton(self.symbol_frame, text=sym, variable=var, command=self.plot_data)
            chk.pack(side=tk.LEFT)
            self.sym_vars[sym] = var
        self.status_var.set("Data loaded")
        self.plot_data()

    def plot_data(
        self,
        predictions: Optional[Dict[str, List[float]]] = None,
        manip_flags: Optional[Dict[str, List[bool]]] = None,
    ) -> None:
        self.ax.clear()
        selected = [s for s, v in self.sym_vars.items() if v.get()] or list(self.data.keys())
        for sym in selected:
            df = self.data.get(sym)
            if df is None:
                continue
            self.ax.plot(df["time"], df["price"], label=f"{sym} price")
            if predictions and sym in predictions:
                self.ax.plot(df["time"], predictions[sym], "--", label=f"{sym} predicted")
            if manip_flags and sym in manip_flags:
                flags = manip_flags[sym]
                times = df["time"][[i for i, f in enumerate(flags) if f]]
                prices = df["price"][[i for i, f in enumerate(flags) if f]]
                self.ax.scatter(times, prices, color="red", marker="o", label=f"{sym} manipulation")
            if "volume" in df.columns:
                self.ax.plot(df["time"], df["volume"], ":", alpha=0.3, label=f"{sym} volume")
            if "open_interest" in df.columns:
                self.ax.plot(df["time"], df["open_interest"], ":", alpha=0.3, label=f"{sym} open interest")
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
        manip_flags: Dict[str, List[bool]] = {}
        total = sum(len(df) for df in self.data.values())
        processed = 0
        self.progress.configure(value=0, maximum=total)
        for sym, df in self.data.items():
            preds: List[float] = []
            flags: List[bool] = []
            for _, row in df.iterrows():
                result = self.detector.process_tick(sym, row.to_dict())
                pred = result.get("prediction")
                preds.append(pred if pred is not None else row["price"])
                flags.append(result.get("manipulation_score", 0) > 0)
                processed += 1
                self.progress.configure(value=processed)
                self.root.update()
            predictions[sym] = preds
            manip_flags[sym] = flags
        self.progress.configure(value=0)
        self.status_var.set("Prediction complete")
        self.plot_data(predictions, manip_flags)

    def run(self) -> None:
        self.root.mainloop()
