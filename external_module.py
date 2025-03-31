from time import sleep
import hvplot.pandas
import pandas as pd
import panel as pn

pn.extension()

data = pd.DataFrame([
    ('Monday', 7), ('Tuesday', 4), ('Wednesday', 9), ('Thursday', 4),
    ('Friday', 4), ('Saturday', 5), ('Sunday', 4)], columns=['Day', 'Wind Speed (m/s)']
)

button = pn.widgets.Button(name="Submit", button_type="primary")

def get_figure(running):
    if not running:
        return "Click Submit"

    sleep(2)
    return data.hvplot(x="Day", y="Wind Speed (m/s)", line_width=10, ylim=(0,10), title="Wind Speed")

bound_function = pn.bind(get_figure, button)
plot = pn.panel(bound_function, height=400, sizing_mode="stretch_width", loading_indicator=True)

pn.Column(button, plot).servable()