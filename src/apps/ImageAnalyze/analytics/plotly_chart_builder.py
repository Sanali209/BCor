from __future__ import annotations

import datetime
from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

from src.apps.ImageAnalyze.gui.utils import format_size


class PlotlyChartBuilder:
    @staticmethod
    def _get_base_layout(title: str, colors: dict[str, str] | None = None) -> go.Layout:
        colors = colors or {}
        bg = colors.get("bg-dark", "#1a1a2e")
        text = colors.get("text-main", "#e0e0e0")
        accent = colors.get("accent-color", "#58a6ff")
        border = colors.get("border-color", "#1f4068")

        return go.Layout(
            title={"text": title, "font": {"color": accent, "size": 16}},
            paper_bgcolor=bg,
            plot_bgcolor=bg,
            font={"color": text},
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor=border),
            yaxis=dict(showgrid=True, gridcolor=border),
            autosize=True,
            legend=dict(font=dict(color=text)),
        )

    @staticmethod
    def _to_html(fig: go.Figure) -> str:
        """Helper to convert figure to full HTML for QWebEngineView.
        Uses include_plotlyjs=True to embed JS for offline usage.
        """
        return pio.to_html(  # type: ignore[no-any-return]
            fig,
            full_html=True,
            include_plotlyjs=True,  # Embed JS directly (safer for restricted environments)
            config={"displayModeBar": False},
        )

    @staticmethod
    def create_format_donut(formats: dict[str, int], colors: dict[str, str] | None = None) -> str:
        colors = colors or {}
        bg = colors.get("bg-dark", "#1a1a2e")
        text = colors.get("text-main", "#e0e0e0")
        border_color = colors.get("border-color", "#16213e")

        if not formats:
            return f"<html><body style='background:{bg}; color:{text}; display:flex; align-items:center; justify-content:center; height:100vh; margin:0;'>No data to display</body></html>"

        labels_with_counts = [f"{k} ({v})" for k, v in formats.items()]
        values = list(formats.values())

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels_with_counts,
                    values=values,
                    hole=0.4,
                    textinfo="percent",
                    hoverinfo="label+value+percent",
                )
            ]
        )

        fig.update_layout(PlotlyChartBuilder._get_base_layout("File Types"))
        fig.update_traces(marker=dict(line=dict(color="#16213e", width=2)))
        return PlotlyChartBuilder._to_html(fig)

    @staticmethod
    def create_size_bar(extension_stats: dict[str, dict[str, Any]], colors: dict[str, str] | None = None) -> str:
        colors = colors or {}
        bar_color = colors.get("bar-color", "#e94560")

        if not extension_stats:
            return "<html><body style='background:#1a1a2e;'></body></html>"

        sorted_exts = sorted(extension_stats.items(), key=lambda x: x[1]["total_size"], reverse=True)[:10]
        exts = [x[0] for x in sorted_exts]
        sizes = [x[1]["total_size"] for x in sorted_exts]
        formatted_sizes = [format_size(s) for s in sizes]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=exts,
                    y=sizes,
                    text=formatted_sizes,
                    textposition="auto",
                    marker_color=bar_color,
                    hovertemplate="%{x}: %{text}<extra></extra>",
                )
            ]
        )

        layout = PlotlyChartBuilder._get_base_layout("Total Size by Format", colors)
        layout.yaxis.title = "Size"
        fig.update_layout(layout)
        return PlotlyChartBuilder._to_html(fig)

    @staticmethod
    def create_resolution_hist(resolution_data: dict[str, list[float]], colors: dict[str, str] | None = None) -> str:
        if not resolution_data or not any(resolution_data.values()):
            return "<html><body style='background:#1a1a2e;'></body></html>"

        data = []
        max_val: float = 0.0
        for ext, mpix_list in resolution_data.items():
            if not mpix_list:
                continue
            max_val = max(max_val, max(mpix_list))
            data.append(
                go.Histogram(x=mpix_list, name=ext, opacity=0.75, xbins=dict(start=0, end=max(max_val, 2), size=2))
            )

        fig = go.Figure(data=data)
        layout = PlotlyChartBuilder._get_base_layout("Megapixels Distribution", colors)
        layout.barmode = "overlay"
        layout.xaxis.title = "Megapixels (MP)"
        layout.yaxis.title = "Count"
        fig.update_layout(layout)
        return PlotlyChartBuilder._to_html(fig)

    @staticmethod
    def create_savings_chart(history: list[dict[str, Any]], colors: dict[str, str] | None = None) -> str:
        colors = colors or {}
        line_color = colors.get("success-color", "#59a14f")

        dates = []
        cumulative = []

        if history:
            history.sort(key=lambda x: x["timestamp"])
            for x in history:
                ts = x["timestamp"]
                try:
                    if isinstance(ts, str):
                        from dateutil import parser  # type: ignore[import-untyped]

                        dt = parser.parse(ts)
                    else:
                        dt = datetime.datetime.fromtimestamp(ts)
                except:
                    dt = datetime.datetime.now()
                dates.append(dt)

            savings = [x["saved_bytes"] for x in history]
            curr = 0
            for s in savings:
                curr += s
                cumulative.append(curr)

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=dates,
                    y=cumulative,
                    mode="lines+markers",
                    fill="tozeroy",
                    name="Total Saved",
                    marker=dict(color=line_color),
                    line=dict(color=line_color, width=3),
                )
            ]
        )

        layout = PlotlyChartBuilder._get_base_layout("Cumulative Space Saved", colors)
        layout.yaxis.title = "Saved Bytes"
        fig.update_layout(layout)
        return PlotlyChartBuilder._to_html(fig)
