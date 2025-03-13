import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import importlib
import os
import glob

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Categories and subcategories navigation structure
def create_nav_structure():
    return {
        "Überblick über Deutschlands Handel": {
            "Gesamtüberblick seit 2008 bis 2024": {
                "Gesamter Export-, Import- und Handelsvolumen-Verlauf Deutschlands": "gesamt_export_import_volumen"
            },
            "Überblick nach bestimmtem Jahr": {
                "Monatlicher Handelsverlauf": "monthly_trade",
                "Top 10 Handelspartner": "top_10_trade_partners",
                "Länder mit größten Export- und Importzuwächsen (absolut)": "top_diff_countries",
                "Länder mit größten Export- und Importzuwächsen (relativ)": "top_growth_countries",
                "Top 10 Waren": "top_10_trade_goods",
                "Waren mit größten Export- und Importzuwächsen (absolut)": "top_diff_goods",
                "Waren mit größten Export- und Importzuwächsen (relativ)": "top_growth_goods"
            }
        },
        "Länderanalyse": {
            "Gesamtüberblick seit 2008 bis 2024": {
                "Gesamter Export-, Import- und Handelsvolumen-Verlauf mit Deutschland": "export_import_with_germany"
            }
        }
    }

categories = create_nav_structure()

def render_sidebar(categories):
    def create_items(subcategories):
        items = []
        for name, value in subcategories.items():
            if isinstance(value, dict):
                items.append(
                    dbc.AccordionItem(
                        dbc.Accordion(create_items(value), start_collapsed=True),
                        title=name
                    )
                )
            else:
                items.append(
                    html.Div(
                        html.A(name, href=f'/{value}', style={"textDecoration": "none", "color": "black", "padding": "5px", "display": "block"})
                    )
                )
        return items
    
    return dbc.Accordion([
        dbc.AccordionItem(
            dbc.Accordion(create_items(subcategories), start_collapsed=True),
            title=category
        )
        for category, subcategories in categories.items()
    ], start_collapsed=True)

sidebar = html.Div([
    html.H2("Navigation", className="display-4"),
    html.Hr(),
    render_sidebar(categories)
], className="sidebar")

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(sidebar, width=3),
            dbc.Col(html.Div(id="page-content"), width=9)
        ])
    ])
])

# Dynamically import graph files and render the content
@app.callback(
    dash.dependencies.Output('page-content', 'children'),
    [dash.dependencies.Input('url', 'pathname')]
)
def render_graph(pathname):
    # Remove the leading '/' from the pathname
    graph_name = pathname.lstrip('/')
    try:
        # Dynamically import the graph module
        graph_module = importlib.import_module(f'graphs.{graph_name}')
        return graph_module.create_layout()
    except ModuleNotFoundError:
        return f"Graph {graph_name} not found", 404

# Registriere Callbacks für alle Graph-Module, die eine register_callbacks-Funktion haben
graph_modules = ['monthly_trade', 'top_10_trade_partners', 'top_diff_countries', 'top_growth_countries', 'top_diff_goods', 'top_growth_goods']  # Liste aller Graphen, die Callbacks haben

for module_name in graph_modules:
    try:
        module = importlib.import_module(f'graphs.{module_name}')
        if hasattr(module, 'register_callbacks'):
            module.register_callbacks(app)
    except ModuleNotFoundError:
        print(f"Module {module_name} not found.")

# Add dcc.Location to allow URL navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),  # Added dcc.Location to track URL
    dbc.Container([
        dbc.Row([
            dbc.Col(sidebar, width=3),
            dbc.Col(html.Div(id="page-content"), width=9)
        ])
    ])
])

if __name__ == "__main__":
    app.run_server(debug=True)
