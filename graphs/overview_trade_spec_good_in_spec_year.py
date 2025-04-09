import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# CSV-Datei einlesen
df = pd.read_csv('data/aggregated_df.csv')

# Funktion zur Formatierung der Y-Achse
def formatter(value):
    if value >= 1e9:
        return f'{value / 1e9:.2f} Mrd'
    elif value >= 1e6:
        return f'{value / 1e6:.0f} Mio'
    elif value >= 1e3:
        return f'{value / 1e3:.0f} K'
    else:
        return str(value)

# Dash-App erstellen
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monatlicher Handelsverlauf für ausgewählte Waren"),

    dcc.Dropdown(
        id='jahr_dropdown',
        options=[{'label': str(j), 'value': j} for j in sorted(df['Jahr'].unique())],
        value=2024,
        clearable=False,
        style={'width': '50%'}
    ),

    dcc.Dropdown(
        id='ware_dropdown',
        options=[{'label': str(w), 'value': w} for w in sorted(df['Label'].unique())],
        value='Mineralische Brennstoffe usw.',
        clearable=False,
        style={'width': '50%'}
    ),

    html.Div(id='info_text', style={'margin-top': '20px', 'font-size': '16px', 'font-weight': 'bold'}),

    dcc.Graph(id='monatlicher_warenhandel_graph'),
])

@app.callback(
    [Output('monatlicher_warenhandel_graph', 'figure'),
     Output('info_text', 'children')],
    [Input('jahr_dropdown', 'value'),
     Input('ware_dropdown', 'value')]
)
def update_graph(year_selected, ware_selected):
    df_filtered = df[(df['Jahr'] == year_selected) & (df['Label'] == ware_selected)]

    fig = go.Figure()

    for col, name, color in zip(
        ['Ausfuhr: Wert', 'Einfuhr: Wert'],
        ['Exportvolumen', 'Importvolumen'],
        ['#1f77b4', '#ff7f0e']
    ):
        fig.add_trace(go.Scatter(
            x=df_filtered['Monat'],
            y=df_filtered[col],
            mode='lines+markers',
            name=name,
            line=dict(width=2, color=color),
            hovertemplate=f'<b>{name}</b><br>Monat: %{{x}}<br>Wert: %{{y:,.0f}} €<extra></extra>'
        ))

    max_value = df_filtered[['Ausfuhr: Wert', 'Einfuhr: Wert']].values.max()

    # # Dynamische Schrittweite für y-Achse
    # if max_value < 5e6:
    #     step = 1e6
    # elif max_value < 10e6:
    #     step = 5e6
    # elif max_value < 50e6:
    #     step = 10e6
    # elif max_value < 100e6:
    #     step = 25e6
    # elif max_value < 250e6:
    #     step = 50e6
    # elif max_value < 500e6:
    #     step = 100e6
    # elif max_value < 1e9:
    #     step = 250e6
    # elif max_value < 5e9:
    #     step = 500e6
    # elif max_value < 10e9:
    #     step = 1e9
    # elif max_value < 50e9:
    #     step = 2e9
    # elif max_value < 100e9:
    #     step = 10e9
    # else:
    #     step = 25e9

        # Dynamische Schrittweite für y-Achse
    if max_value < 1e6:
        step = 100e3
    elif max_value < 5e6:
        step = 500e3
    elif max_value < 10e6:
        step = 1e6
    elif max_value < 50e6:
        step = 5e6
    elif max_value < 100e6:
        step = 10e6
    elif max_value < 250e6:
        step = 25e6
    elif max_value < 500e6:
        step = 50e6
    elif max_value < 1e9:
        step = 100e6
    elif max_value < 2e9:
        step = 250e6
    elif max_value < 5e9:
        step = 500e6
    elif max_value < 10e9:
        step = 1e9
    elif max_value < 50e9:
        step = 2e9
    elif max_value < 100e9:
        step = 10e9
    else:
        step = 25e9


    rounded_max = math.ceil(max_value / step) * step
    tickvals = np.arange(0, rounded_max + 1, step)
    ticktext = [formatter(val) for val in tickvals]

    fig.update_layout(
        title=f'Monatlicher Export- und Importverlauf von {ware_selected} im Jahr {year_selected}',
        xaxis_title='Monat',
        yaxis_title='Wert in €',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        ),
        yaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        legend=dict(title='Kategorie', bgcolor='rgba(255,255,255,0.7)')
    )

    # Ranking-Logik
    df_ranking = df[df['Jahr'] == year_selected].groupby(['Jahr', 'Label'], as_index=False).agg(
        {'Ausfuhr: Wert': 'sum', 'Einfuhr: Wert': 'sum'}
    )

    df_ranking['Export-Rang'] = df_ranking['Ausfuhr: Wert'].rank(method='min', ascending=False)
    df_ranking['Import-Rang'] = df_ranking['Einfuhr: Wert'].rank(method='min', ascending=False)

    selected_product = df_ranking[df_ranking['Label'] == ware_selected]

    if selected_product.empty:
        info_text = f"Keine Daten für {ware_selected} im Jahr {year_selected} verfügbar."
    else:
        export_rank = int(selected_product['Export-Rang'].values[0])
        import_rank = int(selected_product['Import-Rang'].values[0])
        info_text = (f"Unter allen deutschen Import- und Exportwaren belegt die Warengruppe '{ware_selected}' "
                     f"im Jahr {year_selected} den {export_rank}. Platz beim Exportvolumen "
                     f"und den {import_rank}. Platz beim Importvolumen.")

    return fig, info_text

if __name__ == '__main__':
    app.run(debug=True)
