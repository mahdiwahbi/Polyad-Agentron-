from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import Flask
import dash_bootstrap_components as dbc
import dash_daq as daq
from components.resource_charts import ResourceCharts
from components.process_monitor import ProcessMonitor
from components.network_monitor import NetworkMonitor
from components.chat import Chat
from components.notifications import Notifications
import os

# Initialize Flask server
server = Flask(__name__)

# Initialize Dash app
app = Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    suppress_callback_exceptions=True
)

# Create components
charts = ResourceCharts()
process_monitor = ProcessMonitor()
network_monitor = NetworkMonitor()
chat = Chat()
notifications = Notifications()

# Layout components
sidebar = html.Div(
    [
        # Logo and title
        html.Div(
            [
                html.Img(
                    src="https://polyad.ai/logo.png",
                    style={
                        "height": "40px",
                        "margin": "10px",
                        "filter": "brightness(0) invert(1)"
                    }
                ),
                html.H2("Polyad AI", className="display-4", style={"color": "#2ecc71"})
            ],
            className="p-3"
        ),
        
        # Navigation
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="fas fa-tachometer-alt me-2"), " Dashboard"],
                    href="#", active=True
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-chart-line me-2"), " Analytics"],
                    href="#"
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-cogs me-2"), " Settings"],
                    href="#"
                ),
                dbc.NavLink(
                    [html.I(className="fas fa-bell me-2"), " Alerts"],
                    href="#"
                ),
            ],
            vertical=True,
            pills=True
        ),
        
        # Quick actions
        html.Div(
            [
                html.Hr(),
                html.Div(
                    [
                        dbc.Button(
                            "Optimize System",
                            color="success",
                            className="me-2",
                            id="optimize-btn"
                        ),
                        dbc.Button(
                            "Clear Cache",
                            color="warning",
                            className="me-2",
                            id="clear-cache-btn"
                        ),
                        dbc.Button(
                            "Restart Services",
                            color="danger",
                            id="restart-btn"
                        )
                    ],
                    className="p-3"
                )
            ]
        )
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "250px",
        "padding": "20px",
        "background": "#2c3e50",
        "color": "#ecf0f1"
    }
)

# Main content
content = html.Div(
    [
        # Header
        html.Div(
            [
                html.H1("System Overview", className="text-white mb-4"),
                
                # Quick stats
                dbc.Row(
                    [
                        dbc.Col(
                            daq.Gauge(
                                id="cpu-gauge",
                                color={"gradient":True,"ranges":{"green":[0,30],"yellow":[30,70],"red":[70,100]}},
                                value=0,
                                label="CPU Usage",
                                max=100,
                                min=0,
                                size=150
                            ),
                            width=3
                        ),
                        dbc.Col(
                            daq.Gauge(
                                id="memory-gauge",
                                color={"gradient":True,"ranges":{"green":[0,30],"yellow":[30,70],"red":[70,100]}},
                                value=0,
                                label="Memory Usage",
                                max=100,
                                min=0,
                                size=150
                            ),
                            width=3
                        ),
                        dbc.Col(
                            daq.Gauge(
                                id="temperature-gauge",
                                color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
                                value=0,
                                label="Temperature",
                                max=100,
                                min=0,
                                size=150
                            ),
                            width=3
                        ),
                        dbc.Col(
                            daq.Gauge(
                                id="disk-gauge",
                                color={"gradient":True,"ranges":{"green":[0,30],"yellow":[30,70],"red":[70,100]}},
                                value=0,
                                label="Disk Usage",
                                max=100,
                                min=0,
                                size=150
                            ),
                            width=3
                        )
                    ],
                    className="mb-4"
                )
            ],
            style={
                "padding": "20px",
                "background": "#2c3e50",
                "color": "#ecf0f1"
            }
        ),
        
        # Main content area
        html.Div(
            [
                # Resource charts
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(id="cpu-chart"),
                            width=4
                        ),
                        dbc.Col(
                            dcc.Graph(id="ram-chart"),
                            width=4
                        ),
                        dbc.Col(
                            dcc.Graph(id="temperature-chart"),
                            width=4
                        )
                    ],
                    className="mb-4"
                ),
                
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(id="disk-chart"),
                            width=4
                        ),
                        dbc.Col(
                            dcc.Graph(id="network-chart"),
                            width=8
                        )
                    ],
                    className="mb-4"
                ),
                
                # Process monitor
                dbc.Card(
                    [
                        dbc.CardHeader("Active Processes", className="bg-dark text-white"),
                        dbc.CardBody(
                            html.Div(id="process-table"),
                            className="table-responsive"
                        )
                    ],
                    className="mb-4"
                ),
                
                # Chat interface
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H5("AI Assistant", className="mb-0"),
                                dbc.Button(
                                    html.I(className="fas fa-info-circle"),
                                    color="link",
                                    id="chat-info-btn"
                                )
                            ],
                            className="bg-dark text-white d-flex justify-content-between align-items-center"
                        ),
                        dbc.CardBody(
                            html.Div(id="chat-container"),
                            style={"height": "400px", "overflow-y": "auto"}
                        ),
                        dbc.CardFooter(
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="chat-input",
                                        placeholder="Type your message...",
                                        className="bg-dark text-white"
                                    ),
                                    dbc.Button(
                                        "Send",
                                        id="chat-send-btn",
                                        color="success"
                                    )
                                ]
                            )
                        )
                    ],
                    className="mb-4"
                )
            ],
            style={
                "margin-left": "250px",
                "padding": "20px",
                "background": "#2c3e50"
            }
        )
    ]
)

# Notifications
notifications_component = notifications.create_notifications_component()

# Layout
app.layout = html.Div([
    sidebar,
    content,
    notifications_component,
    
    # Update interval
    dcc.Interval(
        id='interval-component',
        interval=2000,  # Update every 2 seconds
        n_intervals=0
    )
])

# Callbacks
@app.callback(
    [Output('cpu-chart', 'figure'),
     Output('ram-chart', 'figure'),
     Output('temperature-chart', 'figure'),
     Output('disk-chart', 'figure'),
     Output('network-chart', 'figure'),
     Output('process-table', 'children'),
     Output('cpu-gauge', 'value'),
     Output('memory-gauge', 'value'),
     Output('temperature-gauge', 'value'),
     Output('disk-gauge', 'value')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    """Update all dashboard components"""
    df = charts.load_metrics()
    
    return (
        charts.create_cpu_chart(df).figure,
        charts.create_ram_chart(df).figure,
        charts.create_temperature_chart(df).figure,
        charts.create_disk_chart(df).figure,
        charts.create_network_chart(df).figure,
        process_monitor.create_process_table(),
        df['cpu_percent'].iloc[-1] if not df.empty else 0,
        df['ram_used_percent'].iloc[-1] if not df.empty else 0,
        df['temperature'].iloc[-1] if not df.empty else 0,
        df['disk_usage'].iloc[-1] if not df.empty else 0
    )

@app.callback(
    Output('chat-container', 'children'),
    [Input('chat-send-btn', 'n_clicks')],
    [State('chat-input', 'value')]
)
def handle_chat(n_clicks, message):
    """Handle chat messages"""
    if not message:
        raise PreventUpdate
    
    response = chat.process_message(message)
    return chat.create_chat_history(message, response)

@app.callback(
    Output("notifications", "children"),
    [Input('interval-component', 'n_intervals')]
)
def update_notifications(n):
    """Update notifications"""
    return notifications.create_notifications()

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)