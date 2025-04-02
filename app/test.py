import panel as pn

pn.extension()

app = pn.Column('hello world v3')

# Serveable entrypoint
app.servable()