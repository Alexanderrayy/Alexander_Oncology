import sys
import traceback
from dash import Dash, dcc, html, dash_table
import dash_leaflet as dl
from dash.dependencies import Input, Output, State 
from PIL import Image, ImageDraw, ImageFont
import io
import base64

from patient_database import OncologyDatabase

print("Libraries imported successfully.")

#This lays out the structure and model

class PatientDataProcessor:
    """Builds an inverted index for quick O(1) filtering of patient records."""
    def __init__(self, raw_data):
        self.data_list = raw_data
        self.inverted_index = {}
        self.filter_keys = ['severity', 'treatment', 'cancer_type']
        self._build_index()

    def _build_index(self):
        if not self.data_list:
            return
        for key in self.filter_keys:
            self.inverted_index[key] = {}
            for i, record in enumerate(self.data_list):
                value = record.get(key)
                if value is not None:
                    if value not in self.inverted_index[key]:
                        self.inverted_index[key][value] = set()
                    self.inverted_index[key][value].add(i)
        print("Inverted Index built for patient filtering.")

    def get_unique_values(self, key):
        return sorted(list(self.inverted_index.get(key, {}).keys()))

    def filter(self, selected_severity, selected_treatment, selected_type):
        if not self.data_list:
            return []

        all_indices = set(range(len(self.data_list)))
        current_match_indices = all_indices.copy()

        filters = {
            'severity': selected_severity,
            'treatment': selected_treatment,
            'cancer_type': selected_type
        }
        
        is_filtered = False
        for key, value in filters.items():
            if value:
                is_filtered = True
                match_set = self.inverted_index[key].get(value)
                if match_set is None:
                    return []
                current_match_indices = current_match_indices.intersection(match_set)
                if not current_match_indices:
                    return []

        if not is_filtered:
            return self.data_list
        return [self.data_list[i] for i in current_match_indices]

#This establishes out connection
print("Connecting to PostgreSQL database...")

db = OncologyDatabase(
    user="postgres",
    password="MrMsAdmin26!", 
    host="db.kpjbkugqexfngdpenybn.supabase.co",
    port=5432, 
    db="postgres"
)

patient_records = db.read_all()

if not patient_records:
    print("WARNING: No data found in the database. Loading dummy data.")
    patient_records = [
        {"patient_id": "P001", "cancer_type": "Melanoma", "severity": "Stage II", "treatment": "Surgery", "location_lat": 34.0522, "location_long": -118.2437},
        {"patient_id": "P002", "cancer_type": "Lung", "severity": "Stage IV", "treatment": "Chemotherapy", "location_lat": 34.0622, "location_long": -118.2537},
        {"patient_id": "P003", "cancer_type": "Breast", "severity": "Stage I", "treatment": "Radiation", "location_lat": 34.0422, "location_long": -118.2337}
    ]
else:
    print(f"Successfully loaded {len(patient_records)} patients from the database!")

data_processor = PatientDataProcessor(patient_records)
columns = list(patient_records[0].keys()) if patient_records else []

severity_options = data_processor.get_unique_values('severity')
treatment_options = data_processor.get_unique_values('treatment')
type_options = data_processor.get_unique_values('cancer_type')

#This is where i create the logo at the top of the app
def create_medical_logo(text="Ray's Oncology Center"):
    width = 450  
    height = 100
    bg_color = (240, 248, 255) 
    text_color = (15, 82, 186) 

    img = Image.new('RGB', (width, height), bg_color)
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    cross_color = (220, 20, 60) 
    d.rectangle([25, 40, 85, 60], fill=cross_color) 
    d.rectangle([45, 20, 65, 80], fill=cross_color) 

    try:
        left, top, right, bottom = d.textbbox((0, 0), text, font=font)
        text_height = bottom - top
    except AttributeError:
        _, text_height = d.textsize(text, font=font)

    text_x = 110  
    text_y = (height - text_height) // 2
    d.text((text_x, text_y), text, fill=text_color, font=font)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    encoded_image = base64.b64encode(img_byte_arr.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded_image}'

logo_url = create_medical_logo()

#This is where we build dynamic layouts
app = Dash(__name__)

def generate_login_layout(error_message=""):
    """Generates the login screen UI."""
    return html.Div([
        html.Div([
            html.Center(html.Img(src=logo_url, height='60px', style={'marginBottom': '20px'})),
            html.H2("Employee Portal Login", style={'textAlign': 'center'}),
            html.Div([
                html.Label("Username", style={'fontWeight': 'bold'}),
                dcc.Input(id='login-username', type='text', style={'width': '100%', 'marginBottom': '10px'}),
                
                html.Label("Password", style={'fontWeight': 'bold'}),
                dcc.Input(id='login-password', type='password', style={'width': '100%', 'marginBottom': '20px'}),
                
                html.Button('Login', id='login-button', n_clicks=0, style={'width': '100%', 'backgroundColor': '#1552ba', 'color': 'white', 'padding': '10px'}),
                
                html.Div(error_message, style={'color': 'red', 'marginTop': '15px', 'textAlign': 'center', 'fontWeight': 'bold'})
            ])
        ], style={'padding': '40px', 'border': '2px solid #a6dcef', 'borderRadius': '10px', 'marginTop': '100px', 'width': '350px'})
    ], style={'display': 'flex', 'justifyContent': 'center'})

def generate_dashboard_layout():
    """Generates the main oncology dashboard UI."""
    return html.Div([
        html.Center([
            html.Img(src=logo_url, height='80px'),
            html.B(html.H1("Alexander's Oncology Patient Geographic & Treatment Dashboard"))
        ]),
        html.Hr(),
        html.Div([
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '10px'}, children=[
                html.Div([
                    html.Label("Cancer Severity", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='severity-dropdown', options=[{'label': s, 'value': s} for s in severity_options], placeholder="Select Severity", clearable=True),
                ]),
                html.Div([
                    html.Label("Treatment Type", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='treatment-dropdown', options=[{'label': t, 'value': t} for t in treatment_options], placeholder="Select Treatment", clearable=True),
                ]),
                html.Div([
                    html.Label("Cancer Type", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='type-dropdown', options=[{'label': c, 'value': c} for c in type_options], placeholder="Select Cancer Type", clearable=True),
                ])
            ]),
            html.Br(),
            html.Div(id='filtered-results', style={'fontSize': '16px', 'fontWeight': 'bold', 'padding': '10px', 'backgroundColor': '#e0f7fa', 'borderRadius': '5px'}),
            html.Label("Patient Distribution by Treatment", style={'marginTop': '20px', 'fontWeight': 'bold'}),
            dcc.Graph(id='treatment-graph')
        ], style={'padding': '10px'}),
        html.Hr(),
        dash_table.DataTable(
            id='datatable-id',
            columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in columns] if columns else [],
            data=patient_records, 
            page_size=10,
            sort_action='native',
            filter_action='native',
            page_action='native',
            fixed_rows={'headers': True},
            style_table={'height': '300px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': 'auto'},
            style_header={'backgroundColor': '#a6dcef', 'fontWeight': 'bold', 'color': '#111'}
        ),
        html.Br(),
        html.Div(id='map-id', style={'height': '500px'})
    ])

# This is how i set the fist layout to be a login screen
app.layout = html.Div(id='page-container', children=generate_login_layout())

#This is the callback
@app.callback(
    Output('page-container', 'children'),
    Input('login-button', 'n_clicks'),
    State('login-username', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True
)
def handle_authentication(n_clicks, username, password):
    if not username or not password:
        return generate_login_layout("Please enter both username and password.")

    role = db.verify_employee(username, password)
    
    if role:
        return generate_dashboard_layout()
    else:
        return generate_login_layout("Invalid credentials. Access denied.")


# 2. This is the filtered callback for the dashboard
@app.callback(
    [Output('datatable-id', 'data'),
     Output('filtered-results', 'children'),
     Output('treatment-graph', 'figure')],
    [Input('severity-dropdown', 'value'),
     Input('treatment-dropdown', 'value'),
     Input('type-dropdown', 'value')]
)
def filter_and_update_display(selected_severity, selected_treatment, selected_type):
    filtered_data = data_processor.filter(selected_severity, selected_treatment, selected_type)
    
    treatment_counts = {}
    for item in filtered_data:
        t_type = item.get('treatment')
        if t_type:
            treatment_counts[t_type] = treatment_counts.get(t_type, 0) + 1
            
    x_values = list(treatment_counts.keys())
    y_values = list(treatment_counts.values())

    figure = {
        'data': [
            {
                'x': x_values,
                'y': y_values,
                'type': 'bar',
                'name': 'Treatment Counts',
                'marker': {'color': ['#4CAF50', '#FFC107', '#2196F3', '#F44336']}
            }
        ],
        'layout': {
            'title': 'Number of Patients per Treatment Plan',
            'xaxis': {'title': 'Treatment Type'},
            'yaxis': {'title': 'Patient Count', 'rangemode': 'tozero'}
        }
    }
    
    status_message = html.P(f"Showing {len(filtered_data)} of {len(data_processor.data_list)} total patients.")
    return filtered_data, status_message, figure

#This calls back the map
@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "data"),
     Input('datatable-id', "active_cell")]
)
def update_map(data, active_cell):
    default_lat = 34.0522
    default_lon = -118.2437
    geo_tile_url = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"

    if active_cell and 'row' in active_cell:
        row_index = active_cell['row']
        if row_index < len(data): 
            selected_row = data[row_index]
            lat = selected_row.get('location_lat')
            lon = selected_row.get('location_long')
            
            if lat and lon:
                return dl.Map(center=[lat, lon], zoom=14, children=[
                    dl.TileLayer(url=geo_tile_url, attribution="&copy; OpenTopoMap contributors"),
                    dl.Marker(position=[lat, lon], draggable=False, children=[
                        dl.Tooltip(f"{selected_row.get('cancer_type')} - {selected_row.get('treatment')}")
                    ])
                ], style={'height': '100%'})
                
    return html.Div([
        dl.Map(center=[default_lat, default_lon], zoom=10, children=[
            dl.TileLayer(url=geo_tile_url, attribution="&copy; OpenTopoMap contributors"),
        ], style={'height': 'calc(100% - 30px)'}),
        html.P("Click on a patient entry in the table to view their location.", style={'color': 'blue', 'padding': '5px'})
    ], style={'height': '100%'})
#this is to confirm and return working server
if __name__ == '__main__':
    print("Starting server at http://127.0.0.1:8055 ...")
    try:
        app.run(debug=True, port=8055) 
    except Exception as e:
        print(f"\nCRITICAL EXECUTION ERROR: {e}")
        traceback.print_exc()   