
from dash import Dash, dcc, html, Input, Output, callback, State, ctx, page_container
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
from path_creator import Vertex, PathCreator
import json
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets, use_pages=True)

app.layout=html.Div([
    dcc.Store(id='clubs-data', storage_type='session'),
    page_container
])

if __name__ == '__main__':
    app.run(debug=True)

