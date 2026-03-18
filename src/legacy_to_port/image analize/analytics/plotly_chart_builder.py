import plotly.graph_objects as go
import plotly.io as pio
from typing import Dict, List, Any
from gui.utils import format_size, format_number

class PlotlyChartBuilder:
    @staticmethod
    def _get_base_layout(title: str) -> go.Layout:
        return go.Layout(
            title={'text': title, 'font': {'color': '#58a6ff', 'size': 16}},
            paper_bgcolor='#1a1a2e',
            plot_bgcolor='#1a1a2e',
            font={'color': '#e0e0e0'},
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(showgrid=True, gridcolor='#1f4068'),
            yaxis=dict(showgrid=True, gridcolor='#1f4068'),
            autosize=True,
            legend=dict(font=dict(color='#e0e0e0'))
        )

    @staticmethod
    def create_format_donut(formats: Dict[str, int]) -> str:
        # Create labels with counts for the legend: "jpg (120)"
        labels_with_counts = [f"{k} ({v})" for k, v in formats.items()]
        values = list(formats.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels_with_counts,
            values=values, 
            hole=.4,
            textinfo='percent', # Show only percent on chart to avoid clutter, label is in legend
            hoverinfo='label+value+percent'
        )])
        
        layout = PlotlyChartBuilder._get_base_layout("File Types")
        fig.update_layout(layout)
        fig.update_traces(marker=dict(line=dict(color='#16213e', width=2)))
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def create_size_bar(extension_stats: Dict[str, Dict[str, Any]]) -> str:
        # Sort by total size
        sorted_exts = sorted(extension_stats.items(), key=lambda x: x[1]['total_size'], reverse=True)
        # Limit to top 10 to avoid clutter
        sorted_exts = sorted_exts[:10]
        
        exts = [x[0] for x in sorted_exts]
        sizes = [x[1]['total_size'] for x in sorted_exts]
        formatted_sizes = [format_size(s) for s in sizes]
        
        fig = go.Figure(data=[go.Bar(
            x=exts,
            y=sizes,
            text=formatted_sizes,
            textposition='auto',
            marker_color='#e94560',
            hovertemplate='%{x}: %{text}<extra></extra>'
        )])
        
        layout = PlotlyChartBuilder._get_base_layout("Total Size by Format")
        layout.yaxis.title = "Size (Bytes)"
        fig.update_layout(layout)
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def create_avg_size_bar(extension_stats: Dict[str, Dict[str, Any]]) -> str:
        # Sort by avg size
        sorted_exts = sorted(extension_stats.items(), key=lambda x: x[1]['avg_size'], reverse=True)
        sorted_exts = sorted_exts[:10]
        
        exts = [x[0] for x in sorted_exts]
        avgs = [x[1]['avg_size'] for x in sorted_exts]
        formatted = [format_size(s) for s in avgs]
        
        fig = go.Figure(data=[go.Bar(
            x=exts,
            y=avgs,
            text=formatted,
            textposition='auto',
            marker_color='#58a6ff',
            hovertemplate='%{x}: %{text}<extra></extra>'
        )])
        
        layout = PlotlyChartBuilder._get_base_layout("Avg File Size")
        fig.update_layout(layout)
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def create_resolution_hist(resolution_data: Dict[str, List[float]]) -> str:
        data = []
        for ext, mpix_list in resolution_data.items():
            if not mpix_list: continue
            data.append(go.Histogram(
                x=mpix_list,
                name=ext,
                opacity=0.75,
                xbins=dict(start=0, end=max(mpix_list) + 1, size=2) # 2MP bins
            ))
            
        fig = go.Figure(data=data)
        
        layout = PlotlyChartBuilder._get_base_layout("Megapixels Distribution")
        layout.barmode = 'overlay'
        layout.xaxis.title = "Megapixels (MP)"
        layout.yaxis.title = "Count"
        fig.update_layout(layout)
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

    @staticmethod
    def create_savings_chart(history: List[Dict[str, Any]]) -> str:
        import datetime
        
        dates = []
        cumulative = []
        
        if history:
            # Sort by timestamp ascending
            history.sort(key=lambda x: x['timestamp'])
            
            timestamps = [x['timestamp'] for x in history]
            dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
            
            # Cumulative Sum
            savings = [x['saved_bytes'] for x in history]
            curr = 0
            for s in savings:
                curr += s
                cumulative.append(curr)
        
        fig = go.Figure(data=[go.Scatter(
            x=dates,
            y=cumulative,
            mode='lines+markers',
            fill='tozeroy',
            name='Total Saved',
            marker=dict(color='#59a14f'),
            line=dict(color='#59a14f', width=3)
        )])
        
        layout = PlotlyChartBuilder._get_base_layout("Cumulative Space Saved")
        layout.yaxis.title = "Saved Bytes"
        fig.update_layout(layout)
        
        return pio.to_html(fig, full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})
