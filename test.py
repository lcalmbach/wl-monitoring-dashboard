import panel as pn

pn.extension()

def hello():
    return pn.pane.Markdown("# Hello, Heroku!", style={'color': 'green'})

app = pn.Column(hello)

# Serveable entrypoint
app.servable()