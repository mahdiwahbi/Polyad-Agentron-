import dash
from dash import dcc, html, dash_table
import psutil
import pandas as pd
from datetime import datetime

class ProcessMonitor:
    def __init__(self):
        """Initialize process monitor"""
        self.max_processes = 10
        
    def get_process_info(self):
        """Get information about top processes by CPU usage"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0:  # Only include active processes
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu': pinfo['cpu_percent'],
                        'memory': round(pinfo['memory_percent'], 1) if pinfo['memory_percent'] else 0,
                        'status': pinfo['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Sort by CPU usage and get top processes
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:self.max_processes]
        
    def create_process_table(self):
        """Create process monitoring table"""
        processes = self.get_process_info()
        
        if not processes:
            return html.Div("No process data available", style={'color': 'white'})
            
        df = pd.DataFrame(processes)
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'PID', 'id': 'pid'},
                {'name': 'Process', 'id': 'name'},
                {'name': 'CPU %', 'id': 'cpu'},
                {'name': 'Memory %', 'id': 'memory'},
                {'name': 'Status', 'id': 'status'}
            ],
            style_header={
                'backgroundColor': '#2c3e50',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': '#34495e',
                'color': 'white'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#2c3e50'
                }
            ],
            style_table={
                'height': '300px',
                'overflowY': 'auto'
            }
        )
