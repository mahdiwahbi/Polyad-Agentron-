import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime

class Notifications:
    def __init__(self):
        self.alerts = []
        self.alert_thresholds = {
            'cpu': 90,
            'memory': 90,
            'temperature': 80,
            'disk': 90,
            'network': 90
        }

    def get_alerts(self):
        """Get current alerts based on metrics"""
        try:
            # Load metrics
            df = pd.read_json('metrics.json')
            
            # Check for alerts
            current_alerts = []
            if not df.empty:
                # CPU Alert
                if df['cpu_percent'].iloc[-1] > self.alert_thresholds['cpu']:
                    current_alerts.append({
                        'type': 'cpu',
                        'value': df['cpu_percent'].iloc[-1],
                        'threshold': self.alert_thresholds['cpu']
                    })
                
                # Memory Alert
                if df['ram_used_percent'].iloc[-1] > self.alert_thresholds['memory']:
                    current_alerts.append({
                        'type': 'memory',
                        'value': df['ram_used_percent'].iloc[-1],
                        'threshold': self.alert_thresholds['memory']
                    })
                
                # Temperature Alert
                if df['temperature'].iloc[-1] > self.alert_thresholds['temperature']:
                    current_alerts.append({
                        'type': 'temperature',
                        'value': df['temperature'].iloc[-1],
                        'threshold': self.alert_thresholds['temperature']
                    })
                
                # Disk Alert
                if df['disk_usage'].iloc[-1] > self.alert_thresholds['disk']:
                    current_alerts.append({
                        'type': 'disk',
                        'value': df['disk_usage'].iloc[-1],
                        'threshold': self.alert_thresholds['disk']
                    })
                
                # Network Alert
                if df['network_usage'].iloc[-1] > self.alert_thresholds['network']:
                    current_alerts.append({
                        'type': 'network',
                        'value': df['network_usage'].iloc[-1],
                        'threshold': self.alert_thresholds['network']
                    })
            
            return current_alerts
            
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

    def create_notifications(self):
        """Create notification components"""
        alerts = self.get_alerts()
        
        if not alerts:
            return html.Div()

        return html.Div([
            dbc.Toast(
                [
                    html.P(
                        f"High {alert['type'].capitalize()} Usage: {alert['value']}% (Threshold: {alert['threshold']}%)",
                        className="mb-0"
                    ),
                    html.Small(
                        datetime.now().strftime("%H:%M:%S"),
                        className="text-muted"
                    )
                ],
                header=alert['type'].capitalize(),
                icon="danger",
                dismissable=True,
                style={"position": "fixed", "top": "80px", "right": "20px"}
            )
            for alert in alerts
        ])

    def add_callbacks(self, app):
        """Add notification callbacks"""
        @app.callback(
            Output("notifications", "children"),
            [Input("interval-component", "n_intervals")]
        )
        def update_notifications(n):
            return self.create_notifications()

    def create_notifications_component(self):
        """Create the notifications container"""
        return html.Div(id="notifications")
