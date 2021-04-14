import dash
import dash_table
from dash_bootstrap_components._components.Col import Col
from dash_bootstrap_components._components.Row import Row
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import json
import plotly.graph_objects as go
import re
import os
import boto3

TOKEN = os.environ.get('mapbox_secret')
ACCESS_KEY = os.environ.get('aws_access_key')
SECRET_KEY = os.environ.get('aws_secret_key')

s3 = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

data_frame = s3.get_object(Bucket='irzelindo-data-viz', Key='data.csv')
map_data = s3.get_object(Bucket='irzelindo-data-viz', Key='map.geojson')

# df = px.data.election()
df = pd.read_csv(data_frame['Body'])
# print(df.head())
df.drop('Unnamed: 0',
        axis='columns', inplace=True)
# print(df.head())
# geojson = px.data.election_geojson()
# df[df.columns[0:]] = df[df.columns[0:]].astype('string')

geojson = json.load(map_data['Body'])

CONFIG = {'displaylogo': False}

# print(df[df['district_id'] == 'Moamba'])

# for feature in geojson['features']:
#     feature['id'] = feature['properties']['fid']

df['iso_alpha'] = [feature['properties']['ISO']
                   for feature in geojson['features']]

df_mean = df.groupby('provinces')[list(
    df.columns[1:7])].mean().apply(lambda a: round(a, 2))

# print(geojson['features'][0])

# candidates = df.winner.unique()
df_table = df.rename(columns={
    'districts': 'District',
    '1997_M': 'Men 1997',
    '1997_W': 'Woman 1997',
    '2007_M': 'Men 2007',
    '2007_W': 'Woman 2007',
    '2017_M': 'Men 2017',
    '2017_W': 'Woman 2017',
    'provinces': 'Province',
})

column_order = [
    'district_id',
    'District',
    'Men 1997',
    'Woman 1997',
    'Men 2007',
    'Woman 2007',
    'Men 2017',
    'Woman 2017',
    'Province',
    'country'
]

df_table = df_table.reindex(columns=column_order)

years = [1997, 2007, 2017]

operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


app = dash.Dash(external_stylesheets=[dbc.themes.MATERIA])

server = app.server

PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(id="search_bar", type="search", placeholder="Search")),
        # dbc.Col(
        #     dbc.Button("Search", color="primary", className="ml-2"),
        #     width="auto",
        # ),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    # dbc.Col(html.Img(src=PLOTLY_LOGO, height="30px")),
                    dbc.Col(dbc.NavbarBrand("Navbar", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="https://plot.ly",
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
    ],
    color="white",
    dark=True,
)

title = dbc.Row(
    [
        dbc.Col([
            html.H3(
                "Premature Mariage Index in Mozambique",
                className="text-center my-3"
            )
        ]
        )
    ],
    align="center"
)

sub_title = dbc.Row(
    [
        dbc.Col([
            html.H3(
                "Men VS Woman",
                className="text-center my-3"
            )
        ]
        )
    ],
    align="center"
)

app.layout = html.Div([
    navbar,
    title,
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='year',
                        options=[{'value': year, 'label': year}
                                 for year in years],
                        value=years[0]
                    ),
                ],
                    width={"size": 4, "offset": 2}),
                dbc.Col([
                    dcc.RadioItems(
                        id='gender',
                        options=[
                            {'label': 'Male', 'value': 'M'},
                            {'label': 'Female', 'value': 'W'},
                        ],
                        value='M',
                        labelStyle={'display': 'inline-block',
                                    'padding-left': 10}
                    ),
                ],
                    width={"size": 4, "offset": 2})
            ]),
            dcc.Graph(
                id="choropleth",
                config=CONFIG
            )
        ], md=6, lg=4),
        
        dbc.Col([
            dbc.Row([
                html.H5(
                    id='province_bar_title'
                )
            ],
                justify="center"
            ),
            dbc.Card([
                dcc.Graph(
                    id="province_bar",
                    config=CONFIG
                )]),
        ], md=6, lg=4),

        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Dropdown(
                        id='province',
                        options=[{'value': province, 'label': province}
                                 for province in df['provinces'].unique()],
                        value=df['provinces'].unique()[0]
                    ),
                ],
                    width={"size": 4, 'offset': 2}),
                dbc.Col([
                    html.H5(id='district_bar_title')
                ], width={"size": 6}),
            ]),
            dcc.Graph(
                id="district_bar",
                config=CONFIG
            )
        ], md=6, lg=4),
    ]),
    html.Hr(),
    sub_title,
    html.Hr(),
    dbc.Row([
        dbc.Col([
        ], width={"size": 6}),
        dbc.Col([
            html.P('''Filter data on table based on text or using >, <, >=, <=...
                   simbols for better analysis. I.E: put <= 15 under Woman 1997 column headeR and hit ENTER.
                   '''
                   )
        ], width={"size": 6})
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dcc.Slider(
                        id='year-slider',
                        min=min(years),
                        max=max(years),
                        value=min(years),
                        marks={str(year): str(year) for year in years},
                        step=None
                    ),
                ], width={"size": 6, "offset": 3}),
            ]),
            dcc.Graph(
                id='men_woman_prov_bar',
                config=CONFIG
            ),
        ], md=6, lg=6),
        dbc.Col([
            dash_table.DataTable(
                id='table-filtering',
                columns=[{"name": i, "id": i} for i in df_table.columns[1:9]],
                data=df_table.to_dict('records'),
                page_size=16,
                page_current=0,
                page_action='custom',

                filter_action='custom',
                filter_query='',

                style_header={
                    'backgroundColor': px.colors.qualitative.Pastel2[7],
                    'fontWeight': 'bold',
                    'fontSize': 13
                },
                style_data_conditional=[
                    {
                        'if': {
                            'filter_query': '{Men 1997} < 18',
                            'column_id': 'Men 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 1997} >= 15 && {Men 1997} < 18',
                            'column_id': 'Men 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 1997} >= 18',
                            'column_id': 'Men 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 1997} < 15',
                            'column_id': 'Woman 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 1997} >= 15 && {Woman 1997} < 18',
                            'column_id': 'Woman 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 1997} >= 18',
                            'column_id': 'Woman 1997'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2007} < 18',
                            'column_id': 'Men 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2007} >= 15 && {Men 2007} < 18',
                            'column_id': 'Men 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2007} >= 18',
                            'column_id': 'Men 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2007} < 18',
                            'column_id': 'Woman 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2007} >= 15 && {Woman 2007} < 18',
                            'column_id': 'Woman 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2007} >= 18',
                            'column_id': 'Woman 2007'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2017} < 18',
                            'column_id': 'Men 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2017} >= 15 && {Men 2017} < 18',
                            'column_id': 'Men 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Men 2017} >= 18',
                            'column_id': 'Men 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2017} < 18',
                            'column_id': 'Woman 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[3],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2017} >= 15 && {Woman 2017} < 18',
                            'column_id': 'Woman 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[1],
                        'color': 'white'
                    },
                    {
                        'if': {
                            'filter_query': '{Woman 2017} >= 18',
                            'column_id': 'Woman 2017'
                        },
                        'backgroundColor': px.colors.qualitative.D3[2],
                        'color': 'white'
                    }
                ]
            )
        ], md=6, lg=6, className="px-4"),
    ]),
])


@app.callback(
    Output('choropleth', 'figure'),
    Input('year', 'value'),
    Input('gender', 'value'))
def display_choropleth(year, gender):
    color = f'{year}_{gender}'
    fig = px.choropleth_mapbox(df,
                               geojson=geojson,  # geojson data to be displayed
                               # column in dataframe should much geojson feature ID
                               locations=df['district_id'],
                               color=color,  # dataframe column to create a colorscale do color the poligons
                               color_continuous_scale='reds_r',
                               #    range_color=[0, 100],
                               opacity=0.8,
                               center={'lat': -19.1637, 'lon': 34.5340},
                               mapbox_style='white-bg',
                               zoom=4,
                               # columns names must appear in the tooltip when hover the poligon
                               hover_data={
                                   'provinces': True, 'iso_alpha': True, 'district_id': False},
                               # data to trigger background events with laco select
                               custom_data=[df['district_id'],
                                            df['districts'], df['provinces']],
                               # title should appear in the tooltip
                               hover_name=df['districts'],
                               # override dataframe column names in legend
                               labels={'iso_alpha': 'Country',
                                       'province': 'Province',
                                       f'{year}_{gender}': 'Age'
                                       }
                               )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0},
                      mapbox_accesstoken=TOKEN)

    return fig


@app.callback(
    Output('province_bar', 'figure'),
    Output('province_bar_title', 'children'),
    Input('year', 'value'),
    Input('gender', 'value')
)
def province(year, gender):
    fig = px.bar(
        df_mean,
        x=df_mean[f'{year}_{gender}'],
        y=df_mean.index,
        orientation='h',
        template='plotly_white',
        color=f'{year}_{gender}',
        color_continuous_scale='reds_r',
        text=f'{year}_{gender}',
        # color_discrete_sequence=[px.colors.qualitative.G10[2], px.colors.qualitative.G10[1]],
        labels={f'{year}_{gender}': 'Age'},
    )
    gender = f'{year}_{gender}'.split('_')
    title = ''
    if gender[1] == 'M':
        title = f'Men index in {gender[0]}/Province'
    elif gender[1] == 'W':
        title = f'Woman index in {gender[0]}/Province'

    return fig, title


@app.callback(
    Output('district_bar', 'figure'),
    Output('district_bar_title', 'children'),
    Input('year', 'value'),
    Input('gender', 'value'),
    Input('province', 'value')
)
def districts(year, gender, province):
    df_districts = df.query(f"provinces=='{province}'")
    fig = px.bar(
        df_districts,
        x=df_districts[f'{year}_{gender}'],
        y=df_districts['districts'],
        orientation='h',
        template='plotly_white',
        color=f'{year}_{gender}',
        color_continuous_scale='reds_r',
        text=f'{year}_{gender}',
        # color_discrete_sequence=[px.colors.qualitative.G10[2], px.colors.qualitative.G10[1]],
        labels={f'{year}_{gender}': 'Age'},
    )

    gender = f'{year}_{gender}'.split('_')
    title = ''
    if gender[1] == 'M':
        title = f'Men in {province} {gender[0]}'
    elif gender[1] == 'W':
        title = f'Woman in {province} {gender[0]}'

    return fig, title


@app.callback(
    Output('men_woman_prov_bar', 'figure'),
    Input('year-slider', 'value')
)
def province_bar(year_slider):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_mean[f'{year_slider}_M'],
        x=df_mean.index,
        name=f'Men {year_slider}',
        orientation='v',
        textposition='outside',
        # width=0.5,
        text=df_mean[f'{year_slider}_M'],
        marker_color=px.colors.qualitative.D3[1],
    ))

    fig.add_trace(go.Bar(
        y=df_mean[f'{year_slider}_W'],
        x=df_mean.index,
        name=f'Womans {year_slider}',
        orientation='v',
        textposition='outside',
        # width=0.5,
        text=df_mean[f'{year_slider}_W'],
        marker_color=px.colors.qualitative.D3[3],
    ))

    # Here we modify the tickangle of the xaxis, resulting in rotated labels.
    fig.update_layout(
        barmode='group',
        height=600,
        # xaxis_tickangle=0,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        # uniformtext_minsize=12,
        bargap=0.1, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1,
        font=dict(
            size=14,
        )
    )

    return fig


@app.callback(
    Output('table-filtering', "data"),
    Input('table-filtering', "page_current"),
    Input('table-filtering', "page_size"),
    Input('table-filtering', "filter_query"))
def update_table(page_current, page_size, filter):
    print(filter)
    filtering_expressions = filter.split(' && ')
    dff = df_table
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(
                filter_value, flags=re.IGNORECASE, regex=True)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    return dff.iloc[
        page_current*page_size:(page_current + 1)*page_size
    ].to_dict('records')

# add callback for toggling the collapse on small screens


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run_server(debug=True)
