
from dash import Dash, dcc, html, Input, Output, callback, State, ctx, page_container, register_page, get_asset_url
import plotly.graph_objs as go
import plotly.express as px
import dash_bootstrap_components as dbc
from path_creator import Vertex, PathCreator
import json
import pandas as pd

register_page(__name__, path='/')

df = None # Dataframe for course
cl = None # Course length
cw = None # Course width

obj_map = {
    'None': 'rgba(0, 0, 0, 0)',
    'Tee': 'rgba(0, 0, 0, 0)',
    'Pin': 'rgba(0, 0, 0, 0)', 
    'Fairway': 'LawnGreen',
    'Rough': 'DarkGreen',
    'Bunker': 'DarkKhaki',
    'Tree':'Olive',
    'Water Hazard':'SteelBlue',
    'Other Obstacle':'Grey'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([html.H1("PickMyClub")]),
        dbc.Col([dcc.Link(html.Img(src=get_asset_url('golf_bag.png'), style={'height': '65px', 'width': '65px'}), href='/bag')], style={
        'position': 'absolute',
        'top': 0,
        'right': 0,
        'margin': '10px'
        })
    ]),
    html.Hr(style={'margin-top': '1px', 'margin-bottom': '5px'}),
    html.P('''Welcome to PickMyClub! This program allows you to build golf holes and vizualize the optimal path from the tee to the pin based on
        your yardages. Start by clicking on the bag icon in the top right to enter your available clubs and respective carry distances. Then, come back here to enter
           the course length and width to proceed with building the course.'''),
    dcc.Input(id='course-length', type='number', placeholder='Course length (yards)', min=0, max=1000),
    dcc.Input(id='course-width', type='number', placeholder='Course width (yards)', min=0, max=1000),
    html.Button('Generate Hole Map', id='start_button', n_clicks=0),
    html.Div(className='row', children=[
        html.Div(children=[
                dbc.Col([
                    dbc.Row(html.B("Select wind intensity"), style={'margin-top':'50px'}),
                    dbc.Row(dcc.Dropdown(options=['None', 'Moderate', 'High'], value='None', id='wind-sel', clearable=False), style={"margin-bottom": "50px"}),
                    dbc.Row([html.B("Construct hole"), html.Abbr("\uFE56", 
                                                                         title="To place hole features, select them below, then place them on the hole map "+
                                                                        "by right-clicking in the desired location. To place a cluster of items (a water hazard, large area of rough, bunker, etc.), "+
                                                                        "you may select a feature below then use the 'Box Select' functionality in the top right of the hole map to place the cluster."
                                                                        , style={'padding-left': 5})]),
                    dbc.Row(dcc.RadioItems(
                        [
                            {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('tee.png'), height=30),
                                        html.Span("Tee", style={'font-size': 15, 'padding-left': 10}),
                                    ],
                                "value": "Tee",
                            },
                            {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('pin.png'), height=30),
                                        html.Span("Pin", style={'font-size': 15, 'padding-left': 10}),
                                    ], 
                                "value": "Pin",
                            },
                            {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('lawngreen.png'), height=20, width=20),
                                        html.Span("Fairway", style={'font-size': 15, 'padding-left': 10})
                                    ],
                                "value": "Fairway",
                            },
                                                        {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('darkgreen.png'),  height=20, width=20),
                                        html.Span("Rough", style={'font-size': 15, 'padding-left': 10})
                                    ],  
                                "value": "Rough",
                            },
                                                        {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('olive.png'),  height=20, width=20),
                                        html.Span("Tree", style={'font-size': 15, 'padding-left': 10})
                                    ],
                                "value": "Tree",
                            },
                                                        {
                               "label":
                                    [
                                        html.Img(src=get_asset_url('darkkhaki.png'),  height=20, width=20),
                                        html.Span("Bunker", style={'font-size': 15, 'padding-left': 10})
                                    ],
                                "value": "Bunker",
                            },
                                                        {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('steelblue.png'),  height=20, width=20),
                                        html.Span("Water Hazard", style={'font-size': 15, 'padding-left': 10})
                                    ],
                                "value": "Water Hazard",
                            },
                                                        {
                                "label":
                                    [
                                        html.Img(src=get_asset_url('grey.png'),  height=20, width=20),
                                        html.Span("Other Obstacle", style={'font-size': 15, 'padding-left': 10})
                                    ],
                                "value": "Other Obstacle",
                            },
                        ],  id='obj-selection', value='Tee')),
                    dbc.Row(html.Button('Reset Hole Features', id='reset_button', n_clicks=0), style={'margin-top':'20px'}),
                    dbc.Row(html.Button('Generate Optimal Path', id='gen_button', n_clicks=0), style={'margin-top':'20px'})
                ]),
                dbc.Col(dcc.Graph(id='basic-interactions')),
                dbc.Col(html.Div(id='path-clubs', style={'margin-top':'50px'}))
            ],
            id = 'graph-div',
            hidden=True
        )
    ]),
])

@callback(
        Output('basic-interactions', 'figure', allow_duplicate=True),
        Input('reset_button', 'n_clicks'),  
        prevent_initial_call=True
)
def reset_graph(n_clicks):
    """
    Resets the graph to all fairway.

    Args:
        n_clicks (int): The number of times the reset button was clicked.

    Returns:
        The new figure.
    """
    global df
    df['obj'] = 'Fairway'
    return get_figure(df)

@callback(
    Output('basic-interactions', 'figure', allow_duplicate=True),
    Output('graph-div', 'style'),
    Input('start_button', 'n_clicks'),
    State('course-length', 'value'),
    State('course-width', 'value'),
    prevent_initial_call=True
)
def generate_initial_graph(n_clicks, new_cl, new_cw):
    """
    Generates the graph from the inputted course length and width.

    Args:
        n_clicks (int): The number of times the start button was clicked.
        new_cl (str): The inputted course length.
        new_cw: The inputted course width.
    
    Returns:
        The new figure, the style of the graph to make it visible.
    """
    global df
    global cl
    global cw

    cl = int(new_cl)
    cw = int(new_cw)

    y_vals = []
    for i in range(cw):
        for _ in range(cl):
            y_vals.append(i)

    x_vals = []
    for _ in range(cw):
        for j in range(cl):
            x_vals.append(j)


    df = pd.DataFrame({
    "x": x_vals,
    "y": y_vals,
    "obj":'Fairway'
    })

    return get_figure(df), {"display": "flex"}
    
@callback(
    Output('basic-interactions', 'figure', allow_duplicate=True),
    Input('basic-interactions', 'clickData'),
    State('obj-selection', 'value'),
    prevent_initial_call=True
)
def clicked_point(clickData, obj_sel):
    """
    Handles changing a point on the graph when it is clicked.

    Args:
        clickData (dict): The data of the user's click.
        obj_sel (str): The selected object to place on the point.

    Returns:
        The new figure.
    """
    global df

    # Get clicked point coordinates
    x = clickData["points"][0]["x"]
    y = clickData["points"][0]["y"]

    # Clear all previous tees or pins if that is what needs to be placed
    if obj_sel == 'Tee' or obj_sel == 'Pin':
        df.loc[df['obj'] == obj_sel, 'obj']='Fairway'

    index_to_update = df.loc[(df['x'] == x) & (df['y'] == y)].index[0]

    # Update the value of "clicked" column 
    df.loc[index_to_update, 'obj'] = obj_sel

    # Add clicked point to the figure data
    return get_figure(df)

@callback(
    Output('basic-interactions', 'figure', allow_duplicate=True),
    Input('basic-interactions', 'selectedData'),
    State('obj-selection', 'value'),
    prevent_initial_call=True
)
def selected_points(selectedData, obj_sel):
    """
    Handles changing points on the graph when they are selected.

    Args:
        selectedData (dict): The data of the user's selection.
        obj_sel (str): The selected object to place on the points.

    Returns:
        The new figure.
    """
    global df

    # Get clicked point coordinates and update dataframe
    for pt in selectedData['points']:
        x = pt["x"]
        y = pt["y"]
        index_to_update = df.loc[(df['x'] == x) & (df['y'] == y)].index[0]

        # Update the value of "clicked" column to True for the found index
        df.loc[index_to_update, 'obj'] = obj_sel

    # Add clicked point to the figure data
    return get_figure(df)

@callback(
    Output('basic-interactions', 'figure', allow_duplicate=True),
    Output('path-clubs', 'children'),
    Input('gen_button', 'n_clicks'),
    State('clubs-data', 'data'),
    State('wind-sel', 'value'),
    prevent_initial_call=True
)
def generate_path(n_clicks, data, wind_val):
    """
    Generates the path on the graph.

    Args:
        n_clicks (int): The number of times that the generate graph button is clicked.
        data (dict): The clubs and their distances.
        wind_val (str): The strength of the wind.

    Returns
        The new figure, an HTML component with the list of clubs to hit.
    """
    # Prepare inputs to PathCreator
    start = df.loc[df['obj'] == 'Tee']
    start = Vertex(start['x'].iloc[0], start['y'].iloc[0])
    end = df.loc[df['obj'] == 'Pin']
    end = Vertex(end['x'].iloc[0], end['y'].iloc[0])

    clubs = {row['club-column']: int(row['dist-column']) for row in data}
    hazard_rows = df[df['obj'].isin(['Tree', 'Water Hazard', 'Other Obstacle'])]
    hazards = list(zip(hazard_rows['x'], hazard_rows['y']))
    wind=wind_val.lower()
    fairway_rows = df[df['obj'] == 'fairway']
    fairways = list(zip(fairway_rows['x'], fairway_rows['y']))
    rough_rows = df[df['obj'] == 'rough']
    roughs = list(zip(rough_rows['x'], rough_rows['y']))
    bunker_rows = df[df['obj'] == 'bunker']
    bunkers = list(zip(bunker_rows['x'], bunker_rows['y']))

    # Calculate optimal path.
    path_creator = PathCreator(cw, cl, hazards, start, end, clubs, wind, fairways, roughs, bunkers)
    path_creator.make_graph(start, end, clubs)
    path, path_clubs = path_creator.run_search()
    path_x = [v.x for v in path]
    path_y = [v.y for v in path]
    fig = get_figure(df, path_x, path_y)

    shot_distances = calc_shot_distances(path_x, path_y)
    clubs_str = []
    clubs_str.append(html.B('Optimal Path', style={'margin-bottom':'10px'}))
    for i in range(1, len(path_clubs)+1):
        clubs_str.append(html.Li("{}: {} yards".format(path_clubs[i-1], shot_distances[i-1])))

    return fig, html.Ol(clubs_str)

def calc_shot_distances(x_vals, y_vals):
    """
    Returns the distances of each shot in the path.

    Args:
        x_vals (list of float): The x values in the path.
        y_vals (lsit of float): The y values in the path.
    """
    distances = []
    for i in range(len(x_vals)-1):
        dist = ((x_vals[i]-x_vals[i+1])**2 + (y_vals[i]-y_vals[i+1])**2)**0.5
        distances.append(int(dist))
    return distances

def get_figure(df, path_x=None, path_y=None):
    """
    Generates a figure from the dataframe.

    Args:
        df (Dataframe): Contains the data of each point.
        path_x (list of float): The x values in the optimal path.
        path_y (list of float): The y values in the optimal path.
    
        Returns:
            The figure.
    """
    fig = px.scatter(df, x="x", y="y", custom_data=["x", "y"], color='obj',color_discrete_map=obj_map)
    fig.update_layout(clickmode='event+select')
    fig.update_traces(opacity=1)
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
        'width': 1200,
        'height': 600
    })
    fig.update_layout(showlegend=False, yaxis_title=None, xaxis_title=None)
    # Add border
    fig.update_xaxes(showline=True,
         linewidth=1,
         linecolor='black',
         mirror=True)
    fig.update_yaxes(showline=True,
         linewidth=1,
         linecolor='black',
         mirror=True)
    
    # Places the tee and pin images
    tee_row = df[df['obj'] == 'Tee']
    pin_row = df[df['obj'] == 'Pin']
    if not tee_row.empty:
        x = tee_row['x'].values[0]
        y = tee_row['y'].values[0]
        fig.add_layout_image(
            dict(
                source=get_asset_url('tee.png'),
                xref="x",
                yref="y",
                xanchor="center",
                yanchor="middle",
                x=x,
                y=y,
                sizex=8,
                sizey=8,
            )
        )
    if not pin_row.empty:
        x = pin_row['x'].values[0]
        y = pin_row['y'].values[0]
        fig.add_layout_image(
            dict(
                source=get_asset_url('pin.png'),
                xref="x",
                yref="y",
                xanchor="center",
                yanchor="middle",
                x=x,
                y=y,
                sizex=8,
                sizey=8,
            )
        )
    
    # Adds the optimal path to the figure (if supplied)
    fig.add_trace(
        go.Scattergl(
            x=path_x,
            y=path_y,
            mode='lines+markers', 
            line=dict(color='black'), 
            marker=dict(color='black', size=10, symbol='square')
        )
    )

    return fig
