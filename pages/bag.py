import dash
from dash import html, dcc, callback, Input, Output, dash_table, State, get_asset_url
import dash_bootstrap_components as dbc
from pathlib import Path
path = Path("bag.py")
path.parent.absolute()

dash.register_page(__name__)


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dbc.Row([
        dbc.Col([html.H1("PickMyClub")]),
        dbc.Col([dcc.Link(html.Img(src=get_asset_url('home.png'), style={'height': '65px', 'width': '65px'}), href='/')], style={
        'position': 'absolute',
        'top': 0,
        'right': 0,
        'margin': '10px'
        })
    ]),
    html.Hr(style={'margin-top': '1px', 'margin-bottom': '5px'}),
    html.P('Add your clubs and respective carry distances to the table below, and go back home by clicking the icon in the top right. You can always come back and make changes to this table.'),
    html.Div([
        dash_table.DataTable(
            id='clubs-table',
            columns=[{
                'name': 'Club',
                'id': 'club-column',
                'deletable': False,
                'renamable': False
            },
            {
                'name': 'Carry Distance',
                'id': 'dist-column',
                'deletable': False,
                'renamable': False
            }],
            data=[{c: '' for c in ('club-column', 'dist-column')}],
            editable=True,
            row_deletable=True,
            style_cell={'textAlign': 'left'}
        ),
        html.Button('Add Club', id='add-club-button', n_clicks=0)
    ], style={'width':1000})
])

@callback(
    Output('clubs-table', 'data', allow_duplicate=True),
    Input('add-club-button', 'n_clicks'),
    State('clubs-table', 'data'),
    State('clubs-table', 'columns'),
    prevent_initial_call='initial_duplicate'
)
def add_row(n_clicks, rows, columns):
    """
    Adds a row to the table.

    Args:
        n_clicks (int): The number of times the add row button was clicked.
        rows (list of {column_id: column_value}): The rows in the table.
        columns (list): The columns in the table.
    """
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@callback(
    Output('clubs-data', 'data'),
    Input('url', 'pathname'),
    State('clubs-table', 'data'),
    prevent_initial_call = True
)
def update_clubs_data(pathname, data):
    """
    Stores the data in the table in the clubs-data dcc.Store component when the url leaves 'bag'.

    Args:
        pathname (str): The path name of the new url.
        data (dict): The data contained in the table.
    """
    return data

@callback(
    Output('clubs-table', 'data'),
    Input('url', 'pathname'),
    State('clubs-data', 'data')    
)
def load_data_from_store(pathname, data):
    """
    Loads the data from the clubs-data dcc.Store component into the table when the url enters 'bag'.

    Args:
        pathname (str): The path name of the new url.
        data (dict): The data contained in the Store component.
    """
    return data