import os
from typing import Any, Type

import pandas as pd
import plotly.express as px
import plotly.io as pio
from vectorbt import Portfolio

from btc_backtest.core.metrics import compute_custom_metrics
from btc_backtest.strategies.base import StrategyBase


class Backtester:
    """
    The Backtester class is responsible for:
    - Accepting a dictionary of OHLCV DataFrames (multiple symbols).
    - Accepting one or more strategies (as class + parameter dict).
    - Running the backtest for each strategy and symbol, saving results and plots.
    """

    def __init__(
        self,
        data_dict: dict[str, pd.DataFrame],
        strategies: list[tuple[Type[StrategyBase], dict[str, Any]]],
        results_dir: str = "results",
    ) -> None:
        self.data_dict = data_dict
        self.strategies = strategies
        self.results_dir = results_dir

        # all_metrics[strategy_name][symbol] -> dict with various metrics
        self.all_metrics: dict[str, dict[str, Any]] = {}
        # all_portfolios[strategy_name][symbol] -> vectorbt.Portfolio object
        self.all_portfolios: dict[str, dict[str, Portfolio]] = {}

        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(os.path.join(self.results_dir, "screenshots"), exist_ok=True)

    def run_all(self) -> None:
        """
        Run the backtest for each strategy on each symbol in self.data_dict,
        and store results (portfolios and metrics).
        """
        for strategy_cls, params in self.strategies:
            strategy_name = strategy_cls.__name__
            self.all_portfolios[strategy_name] = {}
            self.all_metrics[strategy_name] = {}

            for symbol, df in self.data_dict.items():
                strat_instance = strategy_cls(data=df.copy(), **params)
                pf = strat_instance.run_backtest()

                self.all_portfolios[strategy_name][symbol] = pf

                base_metrics = strat_instance.get_metrics()
                extra_metrics = compute_custom_metrics(pf)
                merged_metrics = {
                    "symbol": symbol,
                    **base_metrics,
                    **extra_metrics,
                }
                self.all_metrics[strategy_name][symbol] = merged_metrics

    def save_metrics_to_csv(self, filename: str = "metrics.csv") -> None:
        """
        Save the collected metrics to a CSV file.
        """
        rows = []
        for strategy_name, syms_dict in self.all_metrics.items():
            for symbol, metric_dict in syms_dict.items():
                row = {
                    "strategy": strategy_name,
                    "symbol": symbol,
                    "sharpe_ratio": metric_dict.get("sharpe_ratio"),
                    "drawdown": metric_dict.get("drawdown"),
                    "exposure": metric_dict.get("exposure"),
                    "total_return": metric_dict.get("total_return"),
                    "winrate": metric_dict.get("winrate"),
                    "expectancy": metric_dict.get("expectancy"),
                }
                rows.append(row)

        df_metrics = pd.DataFrame(rows)
        csv_path = os.path.join(self.results_dir, filename)
        df_metrics.to_csv(csv_path, index=False)
        print(f"Metrics saved to {csv_path}")

    def plot_equity_curves(
        self,
        use_log_scale: bool = True,
        template: str = "plotly_white",
        sort_by_final: bool = True,
        top_bottom_n: int = 0,   # 0 = show all
        save_html: bool = False
    ) -> None:
        """
        Plot and save equity curves.
        You can limit lines to top_bottom_n and sort by final value for clarity.
        """
        for strategy_name, syms_dict in self.all_portfolios.items():
            equity_data = []
            for symbol, pf in syms_dict.items():
                series = pf.value()
                final_val = series.iloc[-1] if not series.empty else 0
                equity_data.append((symbol, series, final_val))

            if sort_by_final:
                equity_data.sort(key=lambda x: x[2], reverse=True)

            if top_bottom_n > 0 and len(equity_data) > 2 * top_bottom_n:
                equity_data = equity_data[:top_bottom_n] + equity_data[-top_bottom_n:]

            fig = None
            for idx, (symbol, series, final_val) in enumerate(equity_data):
                if idx == 0:
                    fig = px.line(
                        series,
                        title=f"{strategy_name} - Equity Curves",
                        labels={"value": "Portfolio Value", "index": "Datetime"},
                        template=template
                    )
                    if len(fig.data) > 0:
                        fig.data[0].name = symbol
                else:
                    fig.add_scatter(
                        x=series.index,
                        y=series.values,
                        mode="lines",
                        name=symbol,
                    )

            if fig is not None:
                fig.update_layout(
                    width=1000,
                    height=600,
                    margin=dict(l=40, r=40, t=60, b=40),
                    title_x=0.5
                )
                if use_log_scale:
                    fig.update_yaxes(type="log")
                    fig.update_layout(yaxis_title="Portfolio Value (log scale)")

                if save_html:
                    html_file = os.path.join(
                        self.results_dir, "screenshots", f"{strategy_name}_equity.html"
                    )
                    fig.write_html(html_file)
                    print(f"Equity curves (HTML) saved: {html_file}")
                else:
                    png_file = os.path.join(
                        self.results_dir, "screenshots", f"{strategy_name}_equity.png"
                    )
                    pio.write_image(fig, png_file, format="png", scale=2)
                    print(f"Equity curves (PNG) saved: {png_file}")

    def plot_performance_heatmap(
        self,
        range_color: tuple[float, float] = (None, None),
        metric: str = "sharpe_ratio",
        template: str = "plotly_white",
        sort_symbols_by_mean: bool = True,
    ) -> None:
        """
        Plot a heatmap of the chosen metric across all strategies and symbols.
        You can clamp the color range and/or sort columns by average metric across strategies.
        Set range_color=(None,None) for automatic color scaling.
        """
        strategies_list = list(self.all_metrics.keys())
        symbols_list = sorted(
            set().union(*[self.all_metrics[s].keys() for s in strategies_list])
        )

        if sort_symbols_by_mean and symbols_list:
            symbol_mean = {}
            for sym in symbols_list:
                values = []
                for strat in strategies_list:
                    val = self.all_metrics[strat].get(sym, {}).get(metric, None)
                    if val is not None:
                        values.append(val)
                symbol_mean[sym] = sum(values) / len(values) if values else 0
            # sort descending
            symbols_list.sort(key=lambda s: symbol_mean[s], reverse=True)

        data_for_heatmap = []
        for strategy_name in strategies_list:
            row = []
            for symbol in symbols_list:
                val = None
                if symbol in self.all_metrics[strategy_name]:
                    val = self.all_metrics[strategy_name][symbol].get(metric, None)
                row.append(val)
            data_for_heatmap.append(row)

        df_heatmap = pd.DataFrame(data_for_heatmap, index=strategies_list, columns=symbols_list)

        fig = px.imshow(
            df_heatmap,
            labels=dict(color=metric, x="Symbols", y="Strategies"),
            x=symbols_list,
            y=strategies_list,
            title=f"Heatmap: {metric}",
            template=template,
            color_continuous_scale="Viridis",  # a different palette for clarity            width=1400,
            height=900,
        )
        # If the user explicitly specified a range_color, we limit the range
        if range_color[0] is not None and range_color[1] is not None:
            fig.update_traces(zmin=range_color[0], zmax=range_color[1])

        fig.update_layout(
            margin=dict(l=40, r=40, t=60, b=120),
            title_x=0.5
        )
        # Return labels and decrease font size to reduce clutter
        fig.update_xaxes(side="top", tickangle=45, tickfont=dict(size=8))
        fig.update_yaxes(tickfont=dict(size=8))

        out_file = os.path.join(self.results_dir, "screenshots", f"heatmap_{metric}.png")
        pio.write_image(fig, out_file, format="png", scale=2)
        print(f"Heatmap saved: {out_file}")

    def generate_html_report(self, filename: str = "report.html") -> None:
        """
        Generate an HTML report listing all PNG or HTML files (e.g. equity curves, heatmaps).
        """
        html_content = "<html><head><title>Backtest Report</title></head><body>"
        html_content += "<h1>Backtest Summary</h1>"

        screenshot_dir = os.path.join(self.results_dir, "screenshots")
        file_list = sorted(os.listdir(screenshot_dir))

        for fname in file_list:
            # If it's a PNG file
            if fname.endswith(".png"):
                full_path = os.path.join("results/screenshots", fname)
                html_content += (
                    f'<div style="margin-bottom:15px;">'
                    f'<img src="{full_path}" alt="{fname}" style="max-width:900px;">'
                    f'</div>'
                )
            # If it's an HTML file (interactive)
            elif fname.endswith(".html"):
                full_path = os.path.join("results/screenshots", fname)
                # Here we embed as an iframe
                html_content += (
                    f'<div style="margin-bottom:15px; border:1px solid #ccc;">'
                    f'<iframe src="{full_path}" width="900" height="600"></iframe>'
                    f'</div>'
                )

        html_content += "</body></html>"

        report_path = os.path.join(self.results_dir, filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"HTML report saved: {report_path}")

    def generate_png_plots(
        self,
        use_log_scale: bool = True,
        template: str = "plotly_white",
        sort_by_final: bool = True,
        top_bottom_n: int = 0,
        heatmap_metrics: list[str] = None,
        heatmap_range: tuple[float, float] = (None, None)
    ) -> None:
        """
        Generate PNG plots for:
          1) Equity curves of all strategies (optionally limited/sorted).
          2) Heatmaps for a list of specified metrics.

        Args:
            use_log_scale (bool): Whether to use log scale for equity curves.
            template (str): Plotly template for styling.
            sort_by_final (bool): Sort equity lines by final portfolio value.
            top_bottom_n (int): If >0, show top and bottom N lines only (for clarity).
            heatmap_metrics (List[str]): Which metrics to build heatmaps for.
            heatmap_range (tuple[float, float]): Color range for heatmaps (None=None=auto).
        """
        self.plot_equity_curves(
            use_log_scale=use_log_scale,
            template=template,
            sort_by_final=sort_by_final,
            top_bottom_n=top_bottom_n,
            save_html=False
        )

        if heatmap_metrics is None:
            heatmap_metrics = ["sharpe_ratio"]

        for m in heatmap_metrics:
            self.plot_performance_heatmap(
                range_color=heatmap_range,
                metric=m,
                template=template,
                sort_symbols_by_mean=True
            )
