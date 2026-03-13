from dash import html, dcc
import pandas as pd

def render_simulation_controls():
    """Renders the interactive controls for the simulation."""
    return html.Div([
        html.Div([
            html.I(className="bi bi-sliders2-vertical me-2"),
            "Paramètres de Simulation Scénaristique"
        ], className="sim-header-title"),
        
        html.Div([
            # Control 1: Premium Adjustment
            html.Div([
                html.Label([
                    html.I(className="bi bi-currency-euro me-2"),
                    "Ajustement des Primes (%)"
                ], className="sim-control-label"),
                dcc.Slider(
                    id='sim-premium-mod',
                    min=-20, max=50, step=1, value=0,
                    marks={-20: '-20%', 0: '0', 50: '+50%'},
                    className="sim-slider"
                ),
                html.P("Simuler une hausse ou baisse tarifaire globale sur le portefeuille.", className="sim-control-help")
            ], className="sim-control-block"),

            # Control 2: Prevention Impact (Claims reduction)
            html.Div([
                html.Label([
                    html.I(className="bi bi-shield-check me-2"),
                    "Impact Prévention (-% Sinistres)"
                ], className="sim-control-label"),
                dcc.Slider(
                    id='sim-claim-mod',
                    min=0, max=40, step=1, value=0,
                    marks={0: '0%', 20: '20%', 40: '40%'},
                    className="sim-slider"
                ),
                html.P("Réduction estimée de la fréquence/sévérité via des actions de prévention.", className="sim-control-help")
            ], className="sim-control-block"),
        ], className="sim-controls-grid")
    ], className="sim-panel")

def calculate_simulation_metrics(df, premium_mod, claim_mod):
    """
    Computes delta metrics based on simulation parameters.
    premium_mod: Percentage increase/decrease in premiums.
    claim_mod: Percentage reduction in claims.
    """
    if df.empty:
        return 0, 0, 0, 0, 0, 0

    # Base Metrics
    base_primes = df['montant_prime'].sum()
    base_claims = df['montant_sinistres'].sum()
    base_lr = (base_claims / base_primes * 100) if base_primes > 0 else 0

    # Simulated Metrics
    sim_primes = base_primes * (1 + premium_mod / 100)
    sim_claims = base_claims * (1 - claim_mod / 100)
    sim_lr = (sim_claims / sim_primes * 100) if sim_primes > 0 else 0

    # Deltas
    delta_primes = sim_primes - base_primes
    delta_claims = sim_claims - base_claims
    delta_lr = sim_lr - base_lr

    return base_primes, sim_primes, base_claims, sim_claims, base_lr, sim_lr

def render_simulation_results(df, premium_mod, claim_mod):
    """Renders the comparison cards between current and simulated state."""
    b_p, s_p, b_c, s_c, b_lr, s_lr = calculate_simulation_metrics(df, premium_mod, claim_mod)
    
    def _make_sim_card(title, base_val, sim_val, unit, is_lr=False):
        delta = sim_val - base_val
        is_positive = delta > 0
        # For LR, lower is better. For Primes, higher is better.
        if is_lr:
            sentiment = "success" if delta < 0 else "danger"
            trend_icon = "bi bi-arrow-down-short" if delta < 0 else "bi bi-arrow-up-short"
        else:
            sentiment = "success" if delta > 0 else "danger"
            trend_icon = "bi bi-arrow-up-short" if delta > 0 else "bi bi-arrow-down-short"
            if title == "Charge Sinistres": # Lower claims is better
                sentiment = "success" if delta < 0 else "danger"
                trend_icon = "bi bi-arrow-down-short" if delta < 0 else "bi bi-arrow-up-short"

        return html.Div([
            html.Div(title, className="sim-res-title"),
            html.Div([
                html.Span(f"{base_val:,.0f}{unit}", className="sim-res-base"),
                html.I(className="bi bi-arrow-right mx-2 sim-res-arrow"),
                html.Span(f"{sim_val:,.0f}{unit}", className=f"sim-res-value sentiment-{sentiment}")
            ], className="sim-res-main"),
            html.Div([
                html.I(className=trend_icon),
                f"{abs(delta):,.0f}{unit} ({((sim_val/base_val - 1)*100) if base_val else 0:+.1f}%)"
            ], className=f"sim-res-delta sentiment-{sentiment}")
        ], className="sim-res-card")

    return html.Div([
        _make_sim_card("Primes Totales", b_p, s_p, " €"),
        _make_sim_card("Charge Sinistres", b_c, s_c, " €"),
        _make_sim_card("Loss Ratio (S/P)", b_lr, s_lr, " %", is_lr=True)
    ], className="sim-results-grid")
