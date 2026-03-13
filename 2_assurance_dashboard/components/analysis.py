from dash import html
import pandas as pd

def generate_strategic_insights(df):
    """Generates automated business insights from the current data slice."""
    insights = []

    # 1. Loss Ratio
    total_prime = df['montant_prime'].sum()
    loss_ratio = (df['montant_sinistres'].sum() / total_prime * 100) if total_prime > 0 else 0
    if loss_ratio > 70:
        insights.append({
            'title': "Alerte Rentabilité",
            'text': f"Loss Ratio critique à {loss_ratio:.1f}%.",
            'detail': "Révision des tarifs recommandée.",
            'variant': "danger",
            'icon': "bi bi-exclamation-triangle-fill"
        })
    elif loss_ratio < 40:
        insights.append({
            'title': "Potentiel de Croissance",
            'text': f"Rentabilité excellente ({loss_ratio:.1f}%).",
            'detail': "Baisse de prime envisageable.",
            'variant': "success",
            'icon': "bi bi-graph-up-arrow"
        })

    # 2. Young Risk
    young_risk = df[df['age'] < 30]['nb_sinistres'].mean()
    old_risk   = df[df['age'] > 50]['nb_sinistres'].mean()
    if young_risk > old_risk * 1.5:
        insights.append({
            'title': "Sinistralité Jeunes",
            'text': "Sur-risque identifié (< 30 ans).",
            'detail': "Cibler des actions de prévention.",
            'variant': "warning",
            'icon': "bi bi-person-bounding-box"
        })

    # 3. Bonus/Malus effectiveness
    malus_claims = df[df['bonus_malus'] > 1.0]['nb_sinistres'].mean()
    bonus_claims = df[df['bonus_malus'] <= 0.7]['nb_sinistres'].mean()
    if malus_claims > bonus_claims * 2:
        insights.append({
            'title': "Bonus/Malus Validé",
            'text': "Segmentation efficace du risque.",
            'detail': "Modèle prédictif confirmé.",
            'variant': "info",
            'icon': "bi bi-check2-circle"
        })

    if not insights:
        insights.append({
            'title': "Portefeuille Stable",
            'text': "Aucune anomalie détectée.",
            'detail': "Profil de risque équilibré.",
            'variant': "secondary",
            'icon': "bi bi-shield-check"
        })

    return insights


def render_sidebar_insights(insights):
    """Renders premium mini-insight cards for the sidebar."""
    return html.Div([
        html.P("Insights Stratégiques", className="insight-section-title"),
        html.Div([
            html.Div([
                html.Div([
                    html.Div(
                        html.I(className=ins['icon']),
                        className=f"insight-mini-icon icon-{ins['variant']}"
                    ),
                    html.Span(ins['title'], className="insight-mini-title")
                ], className="insight-mini-header"),
                html.Div(ins['text'],   className="insight-mini-text"),
                html.Div(ins['detail'], className="insight-mini-detail")
            ], className=f"insight-mini insight-{ins['variant']}")
            for ins in insights
        ])
    ])


# ── Global Analysis Panel ──────────────────────────────────────────────────────

def _build_analysis_card(icon, title, value, description, variant, recommendation):
    """Helper to build a single analysis card."""
    return html.Div([
        html.Div([
            html.Div(html.I(className=icon), className=f"ga-card-icon icon-{variant}"),
            html.Div([
                html.Span(title, className="ga-card-title"),
                html.Span(value, className=f"ga-card-value ga-value-{variant}"),
            ], className="ga-card-header-text"),
        ], className="ga-card-header"),
        html.P(description, className="ga-card-desc"),
        html.Div([
            html.I(className="bi bi-lightbulb me-2"),
            recommendation
        ], className=f"ga-card-reco ga-reco-{variant}"),
    ], className=f"ga-card ga-card-border-{variant}")


def render_global_analysis(df):
    """
    Renders a full-width intelligent analysis section at the bottom of the dashboard.
    Synthesises all dimensions of the data into actionable strategic insights.
    """
    if df.empty:
        return html.Div()

    n = len(df)

    # ── Compute metrics ───────────────────────────────────────
    total_prime    = df['montant_prime'].sum()
    total_sinistre = df['montant_sinistres'].sum()
    loss_ratio     = (total_sinistre / total_prime * 100) if total_prime > 0 else 0

    # Loss ratio health
    if loss_ratio > 75:
        lr_variant = "danger"
        lr_value   = f"{loss_ratio:.1f}% ⚠"
        lr_desc    = (f"Le ratio sinistres/primes dépasse le seuil critique de 75 %. "
                      f"Sur {n} contrats, la charge sinistre ({total_sinistre:,.0f} €) érode fortement "
                      f"les primes ({total_prime:,.0f} €).")
        lr_reco    = "Révision immédiate de la tarification et resserrement de la politique de souscription."
    elif loss_ratio > 60:
        lr_variant = "warning"
        lr_value   = f"{loss_ratio:.1f}% ~"
        lr_desc    = (f"Le Loss Ratio est sous surveillance ({loss_ratio:.1f}%). "
                      f"La marge technique reste positive mais fragile.")
        lr_reco    = "Surveiller l'évolution mensuelle et envisager des ajustements tarifaires ciblés."
    else:
        lr_variant = "success"
        lr_value   = f"{loss_ratio:.1f}% ✓"
        lr_desc    = (f"Excellent équilibre technique : {loss_ratio:.1f}% de Loss Ratio sur {n} contrats. "
                      f"La rentabilité brute est solide.")
        lr_reco    = "Capitaliser sur la compétitivité prix pour accélérer la croissance du portefeuille."

    # ── Age / Risk segmentation ───────────────────────────────
    age_group = pd.cut(df['age'], bins=[0, 25, 35, 50, 100],
                       labels=["18-25", "26-35", "36-50", "51+"])
    age_risk  = df.groupby(age_group, observed=True)['nb_sinistres'].mean()
    riskiest_age = age_risk.idxmax() if not age_risk.empty else "N/A"
    riskiest_val = age_risk.max() if not age_risk.empty else 0
    safest_age   = age_risk.idxmin() if not age_risk.empty else "N/A"

    age_variant = "warning" if riskiest_val > df['nb_sinistres'].mean() * 1.4 else "info"
    age_value   = f"Tranche {riskiest_age}"
    age_desc    = (f"L'analyse de la sinistralité par tranche d'âge révèle que les {riskiest_age} ans "
                   f"cumulent en moyenne {riskiest_val:.2f} sinistres/contrat. "
                   f"La tranche la plus saine est {safest_age} ans.")
    age_reco    = (f"Adapter la prime et les franchises pour la tranche {riskiest_age} ans. "
                   f"Fidéliser la tranche {safest_age} ans avec des offres avantageuses.")

    # ── Regional performance ──────────────────────────────────
    reg_perf = df.groupby('region').apply(
        lambda x: x['montant_prime'].sum() - x['montant_sinistres'].sum(), include_groups=False
    ).sort_values(ascending=False)
    top_region    = reg_perf.index[0]  if len(reg_perf) >= 1 else "N/A"
    bottom_region = reg_perf.index[-1] if len(reg_perf) >= 2 else "N/A"
    top_margin    = reg_perf.iloc[0]   if len(reg_perf) >= 1 else 0
    bottom_margin = reg_perf.iloc[-1]  if len(reg_perf) >= 2 else 0

    reg_variant = "danger" if bottom_margin < 0 else "success"
    reg_value   = top_region
    reg_desc    = (f"La région {top_region} est la plus rentable avec une marge brute de "
                   f"{top_margin:,.0f} €. À l'opposé, {bottom_region} affiche "
                   f"{'une perte' if bottom_margin < 0 else 'la plus faible marge'} de {bottom_margin:,.0f} €.")
    reg_reco    = (f"Concentrer les efforts commerciaux sur {top_region}. "
                   f"{'Mettre sous revue la souscription' if bottom_margin < 0 else 'Analyser les opportunités de croissance'} "
                   f"en {bottom_region}.")

    # ── Product mix ───────────────────────────────────────────
    type_lr = df.groupby('type_assurance').apply(
        lambda x: (x['montant_sinistres'].sum() / x['montant_prime'].sum() * 100)
                   if x['montant_prime'].sum() > 0 else 0, include_groups=False
    ).sort_values(ascending=False)
    worst_type  = type_lr.index[0]  if not type_lr.empty else "N/A"
    best_type   = type_lr.index[-1] if len(type_lr) > 1 else "N/A"
    worst_lr    = type_lr.iloc[0]   if not type_lr.empty else 0
    best_lr     = type_lr.iloc[-1]  if len(type_lr) > 1 else 0

    prod_variant = "danger" if worst_lr > 80 else "warning" if worst_lr > 65 else "info"
    prod_value   = f"LR {worst_lr:.0f}%"
    prod_desc    = (f"Le produit '{worst_type}' est le moins rentable avec un Loss Ratio de {worst_lr:.1f}%. "
                    f"À l'inverse, '{best_type}' est le produit le plus équilibré ({best_lr:.1f}%).")
    prod_reco    = (f"Revoir la tarification de '{worst_type}' et renforcer la vente de '{best_type}' "
                    f"auprès des segments à faible risque.")

    # ── Bonus-Malus effectiveness ─────────────────────────────
    malus_mean  = df[df['bonus_malus'] > 1.0]['nb_sinistres'].mean()
    normal_mean = df[(df['bonus_malus'] >= 0.8) & (df['bonus_malus'] <= 1.0)]['nb_sinistres'].mean()
    bonus_mean  = df[df['bonus_malus'] < 0.8]['nb_sinistres'].mean()

    bm_ratio    = (malus_mean / bonus_mean) if (bonus_mean and bonus_mean > 0) else 1
    bm_variant  = "success" if bm_ratio > 1.8 else "warning"
    bm_value    = f"×{bm_ratio:.1f} différentiel"
    bm_desc     = (f"Les assurés en malus (<i>coeff > 1</i>) génèrent {malus_mean:.2f} sinistres/contrat "
                   f"vs {bonus_mean:.2f} en bonus. Le coefficient discrimine "
                   f"{'efficacement' if bm_ratio > 1.8 else 'partiellement'} le risque.")
    bm_reco    = ("Le modèle bonus-malus est un prédicteur robuste : l'utiliser comme variable "
                  "clé dans le scoring actuariel."
                  if bm_ratio > 1.8 else
                  "Enrichir le modèle bonus-malus avec des variables comportementales supplémentaires.")

    # ── Overall verdict ───────────────────────────────────────
    if loss_ratio > 75 or bottom_margin < -50_000:
        verdict_variant = "danger"
        verdict_icon    = "bi bi-exclamation-octagon-fill"
        verdict_title   = "Portefeuille sous Tension — Actions Correctives Urgentes"
        verdict_text    = (f"L'analyse globale de {n} contrats révèle des déséquilibres techniques significatifs. "
                           f"Le Loss Ratio de {loss_ratio:.1f}% et les pertes régionales identifiées "
                           f"nécessitent une intervention rapide sur la politique de souscription et la tarification.")
    elif loss_ratio > 60 or worst_lr > 75:
        verdict_variant = "warning"
        verdict_icon    = "bi bi-exclamation-triangle-fill"
        verdict_title   = "Portefeuille Viable — Optimisation Recommandée"
        verdict_text    = (f"Le portefeuille de {n} contrats est économiquement viable (LR {loss_ratio:.1f}%) "
                           f"mais présente des poches de sous-performance à corrigersur certains produits "
                           f"et régions. Une optimisation ciblée est recommandée.")
    else:
        verdict_variant = "success"
        verdict_icon    = "bi bi-patch-check-fill"
        verdict_title   = "Portefeuille Sain — Stratégie de Croissance"
        verdict_text    = (f"Excellent profil de risque sur {n} contrats. "
                           f"Le Loss Ratio de {loss_ratio:.1f}% offre une marge confortable pour "
                           f"développer de nouvelles lignes de produits et conquérir de nouveaux segments.")

    # ── Build cards ───────────────────────────────────────────
    cards = [
        _build_analysis_card("bi bi-activity",            "Équilibre Technique",       lr_value,    lr_desc,   lr_variant,   lr_reco),
        _build_analysis_card("bi bi-people-fill",         "Risque par Segment d'Âge",  age_value,   age_desc,  age_variant,  age_reco),
        _build_analysis_card("bi bi-geo-alt-fill",        "Performance Régionale",      reg_value,   reg_desc,  reg_variant,  reg_reco),
        _build_analysis_card("bi bi-tag-fill",            "Mix Produit",                prod_value,  prod_desc, prod_variant, prod_reco),
        _build_analysis_card("bi bi-sliders",             "Système Bonus / Malus",      bm_value,    bm_desc,   bm_variant,   bm_reco),
    ]

    return html.Div([
        # Section header
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="bi bi-cpu me-2"),
                    "IA Analytics"
                ], className="header-badge"),
                html.H2("Analyse Globale Intelligente", className="ga-section-title"),
                html.P(
                    "Synthèse automatisée de l'ensemble des indicateurs du portefeuille — recommandations actionnables.",
                    className="ga-section-subtitle"
                ),
            ]),
            html.Div([
                html.I(className=f"{verdict_icon} me-2"),
                html.Span(f"{n} contrats analysés", className="ga-badge-count")
            ], className=f"ga-verdict-badge ga-verdict-{verdict_variant}")
        ], className="ga-section-header"),

        # Cards grid
        html.Div(cards, className="ga-cards-grid"),

        # Global verdict banner
        html.Div([
            html.Div([
                html.I(className=f"{verdict_icon} ga-verdict-icon"),
                html.Div([
                    html.H5(verdict_title, className="ga-verdict-title"),
                    html.P(verdict_text,   className="ga-verdict-text"),
                ])
            ], className="ga-verdict-inner")
        ], className=f"ga-verdict ga-verdict-bg-{verdict_variant}"),

    ], className="ga-section")
