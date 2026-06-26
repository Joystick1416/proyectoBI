"""Layout — Dashboard 3: Gasto Presupuestal.

Placeholder hasta que fact_gasto.parquet esté disponible.
Cuando lleguen los datos, reemplazar este archivo con los callbacks reales.
"""
from dash import html
import dash_bootstrap_components as dbc

C = {
    "bambu":  "#5C8A66",
    "marron": "#665044",
    "musgo":  "#8C9980",
    "naranja":"#D36E36",
}

PASOS = [
    ("1", "Descarga los datos MEF/SIAF",
     "Accede al portal de Consulta Amigable del MEF y descarga la ejecución "
     "presupuestal para la función Saneamiento / Residuos Sólidos, años 2019–2024."),
    ("2", "Coloca el archivo en data/raw/",
     "Guarda el CSV como Gasto_Mantenimiento_Diario.csv (ya tienes el diccionario "
     "de variables en esa carpeta como referencia)."),
    ("3", "Ejecuta el pipeline",
     "Corre: python run_pipeline.py — el ETL construirá fact_gasto.parquet "
     "automáticamente y la base DuckDB se actualizará."),
    ("4", "Recarga la app",
     "Al reiniciar la app este dashboard mostrará los KPIs, el gauge de ejecución, "
     "el calendar heatmap y los gráficos completos."),
]


def layout():
    pasos_cards = [
        html.Div(style={
            "display": "flex", "gap": "16px", "alignItems": "flex-start",
            "padding": "20px", "background": "#FDFAF6", "borderRadius": "10px",
            "marginBottom": "12px", "border": f"1px solid #E8E2DA",
        }, children=[
            html.Div(num, style={
                "background": C["bambu"], "color": "white",
                "borderRadius": "50%", "width": "36px", "height": "36px",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "fontFamily": "Fraunces, serif", "fontSize": "1.1rem",
                "fontWeight": "600", "flexShrink": "0",
            }),
            html.Div([
                html.Div(titulo, style={
                    "fontFamily": "Quicksand, sans-serif", "fontWeight": "700",
                    "fontSize": "0.95rem", "color": C["marron"], "marginBottom": "4px",
                }),
                html.Div(desc, style={
                    "fontFamily": "Quicksand, sans-serif", "fontSize": "0.88rem",
                    "color": "#6B6B6B", "lineHeight": "1.5",
                }),
            ]),
        ])
        for num, titulo, desc in PASOS
    ]

    preview_charts = dbc.Row([
        dbc.Col(html.Div(style={
            "background": "#F5F2EE", "borderRadius": "10px", "padding": "30px",
            "textAlign": "center", "color": C["musgo"],
            "fontFamily": "Caveat, cursive", "fontSize": "1rem",
            "border": "2px dashed #CCC8C0",
        }, children=[
            html.Div("Gauge — % Ejecución nacional", style={
                "fontFamily": "Fraunces, serif", "color": C["marron"],
                "fontSize": "1rem", "marginBottom": "6px",
            }),
            "+ Barras de progreso por departamento",
        ]), md=6),
        dbc.Col(html.Div(style={
            "background": "#F5F2EE", "borderRadius": "10px", "padding": "30px",
            "textAlign": "center", "color": C["musgo"],
            "fontFamily": "Caveat, cursive", "fontSize": "1rem",
            "border": "2px dashed #CCC8C0",
        }, children=[
            html.Div("Calendar Heatmap", style={
                "fontFamily": "Fraunces, serif", "color": C["marron"],
                "fontSize": "1rem", "marginBottom": "6px",
            }),
            "Devengado mensual · estilo GitHub",
        ]), md=6),
    ], className="mb-4")

    return html.Div(style={"padding": "24px"}, children=[
        # Encabezado
        html.Div(style={
            "background": f"linear-gradient(135deg, {C['bambu']}18, {C['naranja']}12)",
            "borderRadius": "12px", "padding": "32px 36px",
            "marginBottom": "24px",
            "borderLeft": f"5px solid {C['bambu']}",
        }, children=[
            html.Div("Gasto Presupuestal MEF/SIAF", style={
                "fontFamily": "Fraunces, serif", "fontSize": "1.6rem",
                "fontWeight": "600", "color": C["marron"], "marginBottom": "8px",
            }),
            html.Div(
                "Este dashboard mostrará la ejecución presupuestal de residuos sólidos "
                "cuando los datos estén disponibles.",
                style={"fontFamily": "Caveat, cursive", "fontSize": "1.1rem",
                       "color": "#6B6B6B"},
            ),
        ]),

        # Preview charts placeholders
        html.Div("Vista previa de gráficos planificados", style={
            "fontFamily": "Fraunces, serif", "fontSize": "1.05rem",
            "color": C["marron"], "marginBottom": "12px",
        }),
        preview_charts,

        # Pasos para activar
        html.Div("Cómo activar este dashboard", style={
            "fontFamily": "Fraunces, serif", "fontSize": "1.05rem",
            "color": C["marron"], "marginBottom": "12px",
        }),
        html.Div(pasos_cards),

        # KPIs planeados
        html.Div("KPIs que se mostrarán", style={
            "fontFamily": "Fraunces, serif", "fontSize": "1.05rem",
            "color": C["marron"], "margin": "20px 0 12px",
        }),
        dbc.Row([
            dbc.Col(html.Div(style={
                "background": "white", "borderRadius": "10px", "padding": "16px",
                "borderLeft": f"4px solid {C['bambu']}",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
            }, children=[
                html.Div("PIA", style={"fontFamily": "Fraunces, serif",
                                       "fontSize": "1.2rem", "color": C["marron"]}),
                html.Div("Presupuesto Institucional de Apertura",
                         style={"fontSize": "0.78rem", "color": "#888",
                                "fontFamily": "Quicksand, sans-serif"}),
            ]), md=3),
            dbc.Col(html.Div(style={
                "background": "white", "borderRadius": "10px", "padding": "16px",
                "borderLeft": f"4px solid {C['naranja']}",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
            }, children=[
                html.Div("PIM", style={"fontFamily": "Fraunces, serif",
                                       "fontSize": "1.2rem", "color": C["marron"]}),
                html.Div("Presupuesto Institucional Modificado",
                         style={"fontSize": "0.78rem", "color": "#888",
                                "fontFamily": "Quicksand, sans-serif"}),
            ]), md=3),
            dbc.Col(html.Div(style={
                "background": "white", "borderRadius": "10px", "padding": "16px",
                "borderLeft": f"4px solid #665044",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
            }, children=[
                html.Div("Devengado", style={"fontFamily": "Fraunces, serif",
                                             "fontSize": "1.2rem", "color": C["marron"]}),
                html.Div("Gasto comprometido y reconocido",
                         style={"fontSize": "0.78rem", "color": "#888",
                                "fontFamily": "Quicksand, sans-serif"}),
            ]), md=3),
            dbc.Col(html.Div(style={
                "background": "white", "borderRadius": "10px", "padding": "16px",
                "borderLeft": f"4px solid {C['musgo']}",
                "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
            }, children=[
                html.Div("% Ejecución", style={"fontFamily": "Fraunces, serif",
                                               "fontSize": "1.2rem", "color": C["marron"]}),
                html.Div("Devengado / PIM × 100",
                         style={"fontSize": "0.78rem", "color": "#888",
                                "fontFamily": "Quicksand, sans-serif"}),
            ]), md=3),
        ]),
    ])
