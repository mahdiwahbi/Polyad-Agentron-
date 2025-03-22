import dash
from dash import dcc, html
import plotly.graph_objs as go
import psutil
from datetime import datetime
import pandas as pd

class NetworkMonitor:
    def __init__(self):
        """Initialize network monitor"""
        self.history_size = 50
        self.bytes_sent_history = []
        self.bytes_recv_history = []
        self.timestamps = []
        self._last_sent = 0
        self._last_recv = 0
        
    def update_network_stats(self):
        """Update network statistics"""
        net_io = psutil.net_io_counters()
        now = datetime.now()
        
        # Calculate speed
        if self._last_sent > 0:
            sent_speed = (net_io.bytes_sent - self._last_sent) / 1024  # KB/s
            recv_speed = (net_io.bytes_recv - self._last_recv) / 1024  # KB/s
        else:
            sent_speed = recv_speed = 0
            
        # Update last values
        self._last_sent = net_io.bytes_sent
        self._last_recv = net_io.bytes_recv
        
        # Update history
        self.bytes_sent_history.append(sent_speed)
        self.bytes_recv_history.append(recv_speed)
        self.timestamps.append(now)
        
        # Keep history size limited
        if len(self.timestamps) > self.history_size:
            self.timestamps.pop(0)
            self.bytes_sent_history.pop(0)
            self.bytes_recv_history.pop(0)
            
    def create_network_chart(self):
        """Create network usage chart"""
        self.update_network_stats()
        
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=self.timestamps,
                        y=self.bytes_sent_history,
                        name='Upload (KB/s)',
                        line={'color': '#27ae60'}
                    ),
                    go.Scatter(
                        x=self.timestamps,
                        y=self.bytes_recv_history,
                        name='Download (KB/s)',
                        line={'color': '#2980b9'}
                    )
                ],
                'layout': go.Layout(
                    title='Network Usage',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'Speed (KB/s)'},
                    template='plotly_dark',
                    showlegend=True
                )
            }
        )
