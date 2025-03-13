import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import numpy as np

def create_layout():
    # CSV file path
    data_file = 'data/1gesamt_deutschland.csv'
    
    # Read data
    df_gesamt_deutschland = pd.read_csv(data_file)

    # Create the graph
    fig = go.Figure()

    # Add traces for Export, Import, and Trade Volume
    for col, name, color in zip(
        ['gesamt_export', 'gesamt_import', 'gesamt_handelsvolumen'],
        ['Exportvolumen', 'Importvolumen', 'Gesamthandelsvolumen'],
        ['#1f77b4', '#ff7f0e', '#2ca02c']
    ):
        fig.add_trace(go.Scatter(
            x=df_gesamt_deutschland['Jahr'],
            y=df_gesamt_deutschland[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Jahr: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    # Calculate Y-axis tick values
    max_value = df_gesamt_deutschland[['gesamt_export', 'gesamt_import', 'gesamt_handelsvolumen']].values.max()
    tick_step = 500e9  # 500 Mrd as step size
    tickvals = np.arange(0, max_value + tick_step, tick_step)

    # Layout settings
    fig.update_layout(
        title='Entwicklung von Export, Import und Handelsvolumen',
        xaxis_title='Jahr',
        yaxis_title='Wert in €',
        yaxis=dict(
            tickformat=',',
            tickvals=tickvals,
            ticktext=[f"{val/1e9:.0f} Mrd" for val in tickvals]
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    return html.Div([
        html.H1("Deutschlands Handelsentwicklung"),
        dcc.Graph(figure=fig)
    ])

