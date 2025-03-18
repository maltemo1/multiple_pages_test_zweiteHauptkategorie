import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
import math
import numpy as np
from multiple_pages_test_zweiteHauptkategorie import app

# Load the data
df_grouped = pd.read_csv('data/df_grouped.csv')

# Unique countries sorted alphabetically
länder_options = sorted(df_grouped['Land'].unique())

# Function for formatting the Y-axis
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.1f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# Create the layout for the graph
def create_layout():
    return html.Div([
        html.H1("Deutschlands Handelsbeziehungen mit anderen Ländern (im Vergleich)"),
        dcc.Dropdown(
            id='land_dropdown',
            options=[{'label': land, 'value': land} for land in länder_options],
            value=['Islamische Republik Iran', 'Irak', 'Katar'],  # Default selection
            multi=True,  # Allow multiple countries to be selected
            clearable=False,
            style={'width': '50%'}
        ),
        html.Div([
            dcc.Graph(id='export_graph'),
            dcc.Graph(id='import_graph'),
            dcc.Graph(id='handelsvolumen_graph')
        ])
    ])

# Callback to update the graphs based on selected countries
@app.callback(
    [Output('export_graph', 'figure'),
     Output('import_graph', 'figure'),
     Output('handelsvolumen_graph', 'figure')],
    Input('land_dropdown', 'value')
)
def update_graph(selected_countries):
    farben = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    export_fig = go.Figure()
    import_fig = go.Figure()
    handelsvolumen_fig = go.Figure()

    for i, country in enumerate(selected_countries):
        df_country = df_grouped[(df_grouped['Land'] == country) &
                                (df_grouped['Jahr'] >= 2008) &
                                (df_grouped['Jahr'] <= 2024)]

        # Export value graph
        export_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['export_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Exportvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

        # Import value graph
        import_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['import_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Importvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

        # Trade volume graph
        handelsvolumen_fig.add_trace(go.Scatter(
            x=df_country['Jahr'],
            y=df_country['handelsvolumen_wert'],
            mode='lines+markers',
            name=country,
            line=dict(width=2, color=farben[i % len(farben)]),
            hovertemplate=f'<b>Gesamthandelsvolumen</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Determine max values for Y-axis and add dynamic steps
    max_export = df_grouped[['export_wert']].max().values[0]
    max_import = df_grouped[['import_wert']].max().values[0]
    max_handelsvolumen = df_grouped[['handelsvolumen_wert']].max().values[0]

    def get_dynamic_ticks(max_value):
        if max_value < 10e6:
            step = 5e6
        elif max_value < 50e6:
            step = 10e6
        elif max_value < 100e6:
            step = 25e6
        elif max_value < 250e6:
            step = 50e6
        elif max_value < 500e6:
            step = 100e6
        elif max_value < 1e9:
            step = 250e6
        elif max_value < 5e9:
            step = 500e6
        elif max_value < 10e9:
            step = 1e9
        elif max_value < 50e9:
            step = 5e9
        elif max_value < 100e9:
            step = 10e9
        else:
            step = 25e9
        rounded_max = math.ceil(max_value / step) * step
        tickvals = np.arange(0, rounded_max + step, step)
        ticktext = [formatter(val) for val in tickvals]
        return tickvals, ticktext

    # Update the Y-axes for each graph
    export_ticks, export_ticktext = get_dynamic_ticks(max_export)
    import_ticks, import_ticktext = get_dynamic_ticks(max_import)
    handelsvolumen_ticks, handelsvolumen_ticktext = get_dynamic_ticks(max_handelsvolumen)

    # Update the layouts for the graphs
    export_fig.update_layout(
        title='Exporte (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=export_ticks, ticktext=export_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    import_fig.update_layout(
        title='Importe (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=import_ticks, ticktext=import_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    handelsvolumen_fig.update_layout(
        title='Handelsvolumen (2008-2024)',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(tickvals=handelsvolumen_ticks, ticktext=handelsvolumen_ticktext),
        legend=dict(title='Länder', bgcolor='rgba(255,255,255,0.7)')
    )

    return export_fig, import_fig, handelsvolumen_fig
