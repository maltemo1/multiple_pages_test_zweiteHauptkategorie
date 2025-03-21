import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import importlib
import os

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
                "Gesamter Export-, Import- und Handelsvolumen-Verlauf mit Deutschland": "LA_gesamt_export_import_volumen",  # Hier hinzugefügt
                "Vergleich mit anderen Ländern": "country_comparison",
                "Export- und Importwachstumsrate": "export_import_growth_countries",
                "Platzierung im Export- und Importranking Deutschlands": "export_import_ranking_graph_of_country",
                "Deutschlands Top 10 Waren im Handel": "#"
            },
            "Überblick nach bestimmtem Jahr": {
                "Handelsbilanz & Ranking": "#",
                "Monatlicher Handelsverlauf": "#",
                "Top 10 Export- und Importwaren": "#",
                "Top 4 Waren nach Differenz zum Vorjahr": "#",
                "Top 4 Waren nach Wachstum zum Vorjahr": "#"
            },
            "Überblick nach bestimmter Ware": {
                "Gesamter Export- und Importverlauf der Ware mit Deutschland": "#"
            },
            "Überblick nach bestimmtem Jahr und Ware": {
                "Monatlicher Verlauf von Export- und Importwerten für die angegebene Ware im Jahr": "#"
            },
            "Überblick nach bestimmtem Zeitraum und Waren": {
                "Export- und Importverlauf (jährlich) bestimmter Waren für ein bestimmtes Land": "#",
                "Export- und Importverlauf (jährlich) einer bestimmten Ware für bestimmte Länder": "#"
            }
        },
        "Warenanalyse": {
            "Gesamtüberblick seit 2008 bis 2024": {
                "Gesamter Export- und Importverlauf der Ware": "#",
                "Deutschlands Top 5 Export- und Importländer der Ware": "#"
            },
            "Überblick mit mehreren Waren über bestimmten Zeitraum": {
                "Gesamter Export- und Importverlauf der Waren (jährliche Werte)": "#",
                "Gesamter Export- und Importverlauf der Waren (monatliche Werte)": "#"
            },
            "Überblick nach bestimmtem Jahr": {
                "Ranking der Ware im Vergleich zu anderen Waren": "#",
                "Monatlicher Export- und Importvolumen-Verlauf der Ware": "#"
            },
            "Überblick nach bestimmtem Land": {
                "Gesamter Export- und Importverlauf der Ware von bzw. nach Deutschland": "#"
            },
            "Überblick nach bestimmtem Zeitraum und Land und Waren": {
                "Export- und Importverlauf (jährlich) mehrerer Waren für ein bestimmtes Land": "#",
                "Export- und Importverlauf (jährlich) einer bestimmten Ware für bestimmte Länder": "#"
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
    dcc.Location(id='url', refresh=False),  # URL Tracker
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
    graph_name = pathname.lstrip('/')
    try:
        graph_module = importlib.import_module(f'graphs.{graph_name}')
        if hasattr(graph_module, 'create_layout'):
            return graph_module.create_layout()
        else:
            return html.Div(f"Graph {graph_name} does not have a create_layout() function"), 404
    except ModuleNotFoundError:
        return html.Div(f"Graph {graph_name} not found"), 404

# Dynamische Registrierung der Callbacks
graph_modules = [
    "gesamt_export_import_volumen",
    "monthly_trade", "top_10_trade_partners", "top_diff_countries", 
    "top_growth_countries", "top_diff_goods", "top_growth_goods", "top_10_trade_goods",
    "LA_gesamt_export_import_volumen", "country_comparison", "export_import_growth_countries", "export_import_ranking_graph_of_country"  # Hier neu hinzugefügt
]

for module_name in graph_modules:
    try:
        module = importlib.import_module(f'graphs.{module_name}')
        if hasattr(module, 'register_callbacks'):
            module.register_callbacks(app)
    except ModuleNotFoundError:
        print(f"Module {module_name} not found.")

if __name__ == "__main__":
    app.run_server(debug=True)
