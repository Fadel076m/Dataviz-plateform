
# Callback JavaScript pour l'impression (Côté Client)
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.print();
        }
        return "";
    }
    """,
    Output('print-dummy', 'children'),
    Input('btn-print', 'n_clicks')
)
