import dash
from dash import dcc, html
import plotly.graph_objs as go
from datetime import datetime, timedelta
import json
import os
import pandas as pd
import psutil
from typing import Optional, Dict, Any

class ResourceCharts:
    def __init__(self):
        self.metrics_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'metrics.json')
        self.alert_thresholds = {
            'cpu': 90,
            'memory': 90,
            'temperature': 80,
            'disk': 90,
            'network': 90
        }
        self.default_metrics = {
            'cpu_percent': 0,
            'ram_used_percent': 0,
            'temperature': 0,
            'disk_usage': 0,
            'network_in': 0,
            'network_out': 0
        }
        
    def load_metrics(self) -> Optional[pd.DataFrame]:
        """Load metrics from JSON file"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    metrics = json.load(f)
                
                if not metrics:
                    return pd.DataFrame([self.default_metrics])
                    
                df = pd.DataFrame(metrics)
                
                # Convert timestamp to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Extract all metrics
                df['cpu_percent'] = df.apply(lambda x: x['cpu']['percent'], axis=1)
                df['ram_used_percent'] = df.apply(lambda x: x['memory']['percent'], axis=1)
                df['temperature'] = df.apply(lambda x: x['temperature'], axis=1)
                df['disk_usage'] = df.apply(lambda x: x['disk']['percent'], axis=1)
                df['network_in'] = df.apply(lambda x: x['network']['bytes_recv'], axis=1)
                df['network_out'] = df.apply(lambda x: x['network']['bytes_sent'], axis=1)
                
                return df
            
            # Return default metrics if file doesn't exist
            return pd.DataFrame([self.default_metrics])
            
        except Exception as e:
            print(f"Error loading metrics: {e}")
            return pd.DataFrame([self.default_metrics])
            
    def create_cpu_chart(self, df: pd.DataFrame) -> dcc.Graph:
        """Create CPU usage chart with alerts"""
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['cpu_percent'],
                        name='CPU %',
                        line={'color': '#2ecc71'},
                        hovertemplate='%{y:.1f}%'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=[self.alert_thresholds['cpu']] * len(df),
                        name='Alert Threshold',
                        line={'color': 'red', 'dash': 'dash'},
                        hovertemplate='Alert Threshold: %{y:.1f}%'
                    )
                ],
                'layout': go.Layout(
                    title='CPU Usage',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'CPU %'},
                    template='plotly_dark',
                    legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
                    margin={'t': 50, 'b': 50, 'l': 50, 'r': 50}
                )
            }
        )
        
    def create_ram_chart(self, df: pd.DataFrame) -> dcc.Graph:
        """Create RAM usage chart with alerts"""
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['ram_used_percent'],
                        name='RAM %',
                        line={'color': '#3498db'},
                        hovertemplate='%{y:.1f}%'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=[self.alert_thresholds['memory']] * len(df),
                        name='Alert Threshold',
                        line={'color': 'red', 'dash': 'dash'},
                        hovertemplate='Alert Threshold: %{y:.1f}%'
                    )
                ],
                'layout': go.Layout(
                    title='RAM Usage',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'RAM %'},
                    template='plotly_dark',
                    legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
                    margin={'t': 50, 'b': 50, 'l': 50, 'r': 50}
                )
            }
        )
        
    def create_temperature_chart(self, df: pd.DataFrame) -> dcc.Graph:
        """Create temperature chart with alerts"""
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['temperature'],
                        name='Temperature',
                        line={'color': '#e74c3c'},
                        hovertemplate='%{y:.1f}°C'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=[self.alert_thresholds['temperature']] * len(df),
                        name='Alert Threshold',
                        line={'color': 'red', 'dash': 'dash'},
                        hovertemplate='Alert Threshold: %{y:.1f}°C'
                    )
                ],
                'layout': go.Layout(
                    title='CPU Temperature',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'Temperature (°C)'},
                    template='plotly_dark',
                    legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
                    margin={'t': 50, 'b': 50, 'l': 50, 'r': 50}
                )
            }
        )
        
    def create_disk_chart(self, df: pd.DataFrame) -> dcc.Graph:
        """Create disk usage chart"""
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['disk_usage'],
                        name='Disk Usage',
                        line={'color': '#9b59b6'},
                        hovertemplate='%{y:.1f}%'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=[self.alert_thresholds['disk']] * len(df),
                        name='Alert Threshold',
                        line={'color': 'red', 'dash': 'dash'},
                        hovertemplate='Alert Threshold: %{y:.1f}%'
                    )
                ],
                'layout': go.Layout(
                    title='Disk Usage',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'Disk Usage %'},
                    template='plotly_dark',
                    legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
                    margin={'t': 50, 'b': 50, 'l': 50, 'r': 50}
                )
            }
        )
        
    def create_network_chart(self, df: pd.DataFrame) -> dcc.Graph:
        """Create network usage chart"""
        return dcc.Graph(
            figure={
                'data': [
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['network_in'],
                        name='Download',
                        line={'color': '#3498db'},
                        hovertemplate='%{y:.2f} bytes/s'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['network_out'],
                        name='Upload',
                        line={'color': '#e74c3c'},
                        hovertemplate='%{y:.2f} bytes/s'
                    ),
                    go.Scatter(
                        x=df['timestamp'],
                        y=[self.alert_thresholds['network']] * len(df),
                        name='Alert Threshold',
                        line={'color': 'red', 'dash': 'dash'},
                        hovertemplate='Alert Threshold: %{y:.1f} bytes/s'
                    )
                ],
                'layout': go.Layout(
                    title='Network Usage',
                    xaxis={'title': 'Time'},
                    yaxis={'title': 'Bytes/s'},
                    template='plotly_dark',
                    legend={'yanchor': 'top', 'y': 0.99, 'xanchor': 'left', 'x': 0.01},
                    margin={'t': 50, 'b': 50, 'l': 50, 'r': 50}
                )
            }
        )
        
    def create_process_table(self, df: pd.DataFrame) -> html.Table:
        """Create process table"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'PID': proc.info['pid'],
                        'Name': proc.info['name'],
                        'CPU': f"{proc.info['cpu_percent']:.1f}%",
                        'Memory': f"{proc.info['memory_percent']:.1f}%"
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return html.Table(
                className='table table-dark table-striped',
                children=[
                    html.Thead(
                        html.Tr([
                            html.Th('PID'),
                            html.Th('Process Name'),
                            html.Th('CPU Usage'),
                            html.Th('Memory Usage')
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(proc['PID']),
                            html.Td(proc['Name']),
                            html.Td(proc['CPU']),
                            html.Td(proc['Memory'])
                        ]) for proc in sorted(processes, key=lambda x: x['CPU'], reverse=True)
                    ])
                ]
            )
        except Exception as e:
            return html.Table(
                className='table table-dark',
                children=[
                    html.Thead(
                        html.Tr([
                            html.Th('Error'),
                            html.Th('Message')
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td('Process Monitoring'),
                            html.Td(str(e))
                        ])
                    ])
                ]
            )
        
    def create_layout(self) -> html.Div:
        """Create dashboard layout"""
        df = self.load_metrics()
        
        if df is None:
            return html.Div("Error loading metrics", style={'color': 'white', 'textAlign': 'center'})
            
        return html.Div([
            # Header
            html.Div([
                html.H1("Polyad System Monitor", 
                        style={'textAlign': 'center', 'color': 'white', 'marginBottom': 30}),
                html.Hr(style={'borderColor': '#2c3e50'})
            ]),
            
            # Resource Charts
            html.Div([
                html.H2("System Resources", style={'color': 'white', 'marginBottom': 20}),
                html.Div([
                    html.Div([
                        self.create_cpu_chart(df)
                    ], className='four columns'),
                    
                    html.Div([
                        self.create_ram_chart(df)
                    ], className='four columns'),
                    
                    html.Div([
                        self.create_temperature_chart(df)
                    ], className='four columns')
                ], className='row'),
                
                html.Div([
                    html.Div([
                        self.create_disk_chart(df)
                    ], className='four columns'),
                    
                    html.Div([
                        self.create_network_chart(df)
                    ], className='eight columns')
                ], className='row')
            ]),
            
            # Process Monitor
            html.Div([
                html.H2("Active Processes", style={'color': 'white', 'marginTop': 30, 'marginBottom': 20}),
                self.create_process_table(df)
            ]),
            
            # Update interval
            dcc.Interval(
                id='interval-component',
                interval=2000,  # Update every 2 seconds
                n_intervals=0
            )
        ], style={'padding': '20px'})