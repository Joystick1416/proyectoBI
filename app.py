"""
app.py — Gestión de Residuos Sólidos · Perú 2019–2024
Ejecutar localmente: python app.py
Deploy Render:       gunicorn app:server
"""
import pandas as _pd  # noqa: F401 — precarga antes de dash/plotly para evitar circular import

import dash
import dash_bootstrap_components as dbc
from dash import html

from layouts.general  import layout as layout_general
from layouts.residuos import layout as layout_residuos
from layouts.gasto    import layout as layout_gasto

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Residuos Sólidos · Perú",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ── Navbar ────────────────────────────────────────────────────────────────────
_navbar = html.Div(
    className="navbar-custom",
    style={"display": "flex", "alignItems": "center", "gap": "12px"},
    children=[
        html.Span("♻", style={"fontSize": "1.6rem"}),
        html.Div([
            html.Span("Gestión de Residuos Sólidos", className="navbar-brand-title"),
            html.Span("Perú · 2019–2024", className="navbar-subtitle"),
        ]),
    ],
)


def serve_layout():
    """
    Dash llama a esta función en cada request inicial.
    Así las queries a DuckDB se ejecutan después de que pandas
    esté completamente cargado, evitando la circular import.
    """
    return html.Div([
        _navbar,
        dbc.Tabs(
            id="tabs-principal",
            active_tab="tab-general",
            children=[
                dbc.Tab(
                    label="General",
                    tab_id="tab-general",
                    label_style={"fontFamily": "Quicksand, sans-serif"},
                    children=layout_general(),
                ),
                dbc.Tab(
                    label="Residuos",
                    tab_id="tab-residuos",
                    label_style={"fontFamily": "Quicksand, sans-serif"},
                    children=layout_residuos(),
                ),
                dbc.Tab(
                    label="Gasto",
                    tab_id="tab-gasto",
                    label_style={"fontFamily": "Quicksand, sans-serif"},
                    children=layout_gasto(),
                ),
            ],
        ),
    ])


app.layout = serve_layout

if __name__ == "__main__":
    app.run(debug=True, port=8050)
