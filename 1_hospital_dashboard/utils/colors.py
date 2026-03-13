# color_palette.py
"""
Palette de couleurs médicales professionnelles pour les visualisations
"""

# Palette principale médicale
MEDICAL_COLORS = {
    'primary': '#3498db',      # Bleu médical (confiance, professionnalisme)
    'primary_light': '#5dade2',
    'primary_dark': '#1a6ecc',
    
    'secondary': '#2ecc71',    # Vert santé (bien-être, positif)
    'secondary_light': '#58d68d',
    'secondary_dark': '#27ae60',
    
    'accent': '#e74c3c',       # Rouge alerte (attention, critique)
    'accent_light': '#ec7063',
    'accent_dark': '#c0392b',
    
    'warning': '#f39c12',      # Orange attention
    'warning_light': '#f5b041',
    'warning_dark': '#d35400',
    
    'info': '#9b59b6',         # Violet (innovation)
    'info_light': '#bb8fce',
    'info_dark': '#8e44ad',
    
    'success': '#1abc9c',      # Turquoise (succès)
    'success_light': '#48c9b0',
    'success_dark': '#16a085',
    
    'dark': '#2c3e50',         # Gris foncé (texte)
    'light': '#ecf0f1',        # Gris clair (arrière-plan)
    'white': '#ffffff'
}

# Palette pour les pathologiques spécifiques
PATHOLOGY_COLORS = {
    'Cancer': MEDICAL_COLORS['accent'],      # Rouge pour Cancer
    'Infarctus': MEDICAL_COLORS['warning'],  # Orange pour Infarctus
    'Fracture': MEDICAL_COLORS['info'],      # Violet pour Fracture
    'Alzheimer': MEDICAL_COLORS['primary'],  # Bleu pour Alzheimer
    'Pneumonie': MEDICAL_COLORS['secondary'], # Vert pour Pneumonie
    'Hypertension': MEDICAL_COLORS['dark'],  # Gris foncé pour Hypertension
    'Eczéma': MEDICAL_COLORS['success']      # Turquoise pour Eczéma
}

# Palette pour les départements
DEPARTMENT_COLORS = {
    'Cardiologie': MEDICAL_COLORS['accent'],
    'Oncologie': MEDICAL_COLORS['primary'],
    'Neurologie': MEDICAL_COLORS['info'],
    'Orthopédie': MEDICAL_COLORS['warning'],
    'Pneumologie': MEDICAL_COLORS['secondary'],
    'Gériatrie': MEDICAL_COLORS['success'],
    'Dermatologie': MEDICAL_COLORS['dark']
}

# Palette séquentielle pour les âges
AGE_GROUP_COLORS = {
    '0-18': MEDICAL_COLORS['primary_light'],
    '19-35': MEDICAL_COLORS['primary'],
    '36-60': MEDICAL_COLORS['primary_dark'],
    '60+': MEDICAL_COLORS['dark']
}

# Configuration des graphiques
GRAPH_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'dashboard_hospitalier',
        'height': 600,
        'width': 1200,
        'scale': 2
    },
    'responsive': True
}

# Template Plotly personnalisé
def create_custom_template():
    import plotly.graph_objects as go
    
    return go.layout.Template(
        layout=go.Layout(
            font=dict(
                family="Segoe UI, -apple-system, BlinkMacSystemFont, sans-serif",
                size=12,
                color=MEDICAL_COLORS['dark']
            ),
            title=dict(
                font=dict(size=16, color=MEDICAL_COLORS['dark']),
                x=0.05,
                xanchor='left'
            ),
            plot_bgcolor=MEDICAL_COLORS['white'],
            paper_bgcolor=MEDICAL_COLORS['white'],
            hoverlabel=dict(
                bgcolor=MEDICAL_COLORS['white'],
                font_size=12,
                font_color=MEDICAL_COLORS['dark']
            ),
            legend=dict(
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor=MEDICAL_COLORS['light'],
                borderwidth=1
            ),
            colorway=list(MEDICAL_COLORS.values())[:6]
        )
    )

CUSTOM_TEMPLATE = create_custom_template()