from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px
import geopandas as gpd

app = Flask(__name__)



# Load data
df = pd.read_csv('data/dataset.csv')
sdf=pd.read_csv('data/dataset.csv')
@app.route('/')
def index():
    states = df['Area name'].unique()
    area_types = df['Total/Rural/Urban'].unique()
    return render_template('index.html', states=states, area_types=area_types)

@app.route('/home')
def home():
    return render_template('index.html')

def draw_pie_chart(male_count, female_count):
    
    labels = ['Male', 'Female']
    values = [male_count, female_count]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])

    fig.update_layout(title='Gender Distribution')

    # Convert figure to JSON
    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json


def bar_chart(dataset, params, region, area_type):
    fig = go.Figure()
    total_pop = dataset[dataset['Education level'] == 'Total'][f'total {params}'].values[0]
    total_pop_list = [total_pop] * dataset.shape[0]
    if not dataset.empty:
        total_persons = dataset['total ' + params].astype(float)
        total_employed = ((dataset[params + ' main worker'].astype(float) + dataset[params + ' marginal worker'].astype(float)) / total_persons) * 100
        total_unemployed = ((dataset[params + ' unemployed'].astype(float) + dataset[params + ' MAW'].astype(float)) / total_persons) * 100
        fig.add_trace(go.Bar(x=dataset['Education level'], y=(total_persons / total_pop_list) * 100, name='Total %', width=0.25, marker_color='rgb(55, 83, 109)'))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=total_unemployed, name='Unemployed %', width=0.25, marker_color='rgb(255, 99, 71)'))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=total_employed, name='Employed %', width=0.25, marker_color='rgb(50, 205, 50)'))

        fig.update_layout(
            barmode='group',
            title={
                'text': f'{region} ({area_type}) {params} Education and Workforce Data',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis_title={
                'text': 'Education Level',
                'font': dict(size=16)
            },
            yaxis_title={
                'text': 'Percentage',
                'font': dict(size=16)
            },
            width=1200,
            height=700,
            showlegend=True,
            legend=dict(
                font=dict(size=14),
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            plot_bgcolor='white',
            xaxis=dict(
                tickfont=dict(size=12),
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            yaxis=dict(
                tickfont=dict(size=12),
                showgrid=True,
                gridwidth=1,
                gridcolor='lightgray'
            ),
            margin=dict(l=50, r=50, t=80, b=50)
        )
    else:
        fig.update_layout(
            title="No data available for this state and area type.",
            width=1200,
            height=700
        )
    fig_json_total = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json_total

def calculate_literacy_rate(data):
    total_data = data[data['Education level'] == 'Total']
    literate_data = data[data['Education level'].isin(['Below Primary', 'Primary', 'Middle', 'Secondary', 'Higher Secondary', 'Graduate & Above'])]
    
    literacy_rates = {}
    for state in total_data['Area name'].unique():
        total_pop = total_data[total_data['Area name'] == state]['total person'].values[0]
        literate_pop = literate_data[literate_data['Area name'] == state]['total person'].sum()
        literacy_rates[state] = (literate_pop / total_pop) * 100
    
    return literacy_rates

def create_literacy_map(literacy_rates):
    # Convert literacy_rates dictionary to DataFrame
    literacy_df = pd.DataFrame.from_dict(literacy_rates, orient='index', columns=['literacy_rate'])
    literacy_df.index.name = 'state'
    literacy_df = literacy_df.reset_index()
    
    # Create choropleth map using plotly express
    fig = px.choropleth(
        literacy_df,
        locations='state',
        locationmode='geojson-id',
        scope="asia",
        center={"lat": 20.5937, "lon": 78.9629},
        color='literacy_rate',
        color_continuous_scale='RdYlGn',
        range_color=(0, 100),
        hover_name='state',
        hover_data={'literacy_rate': ':.2f'},
        labels={'literacy_rate': 'Literacy Rate (%)'},
        title='Literacy Rate by State',
    )
    
    fig.update_geos(
        visible=False,
        resolution=50,
        showcountries=True,
        countrycolor="Black",
        showsubunits=True,
        subunitcolor="Black",
        fitbounds="locations"
    )
    
    fig.update_layout(
        title_x=0.5,
        width=800,
        height=600,
        margin={"r":0,"t":30,"l":0,"b":0},
        geo=dict(
            lonaxis_range=[ 68, 98 ],
            lataxis_range=[ 6, 38 ],
            projection_scale=4
        )
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/visualize', methods=['POST'])
def visualize():
    state = request.form.get('state')
    area_type = request.form.get('area_type')
    
    # Calculate literacy rates for all states
    total_data = df[df['Total/Rural/Urban'] == 'Total']
    literacy_rates = calculate_literacy_rate(total_data)
    
    # Create map using geopandas
    map_json = create_literacy_map(literacy_rates)
    
    # Existing visualization code
    state_data = df[(df['Area name'] == state) & (df['Total/Rural/Urban'] == area_type)]
    fig_json_total = bar_chart(state_data,'person',state,area_type)
    fig_json_males = bar_chart(state_data,'males',state,area_type)
    fig_json_females = bar_chart(state_data,'females',state,area_type)

    male_count = state_data[state_data["Education level"]=="Total"]["total males"].iloc[0]
    female_count = state_data[state_data["Education level"]=="Total"]["total females"].iloc[0]
    print(type(male_count))
    gender_pie_json=draw_pie_chart(male_count,female_count)

    global sdf
    sdf = pd.read_csv('data/states_data/'+state.title()+".csv")
    districts = sdf['Area name'].unique()
    dist_area_types = sdf['Total/Rural/Urban'].unique()
    
    data_dict = {
        'fig_json': fig_json_total,
        'fig_json_males': fig_json_males,
        'fig_json_females': fig_json_females,
        'gender_pie_json':gender_pie_json,
        'state': state,
        'district': districts,
        'dist_area_types': dist_area_types,
        'map_json': map_json
    }
    return render_template('visualization.html', data=data_dict)

@app.route('/visualize_dist', methods=['POST'])
def visualize_dist():
    global sdf
    district = request.form.get('district')
    area_type = request.form.get('area_type')
    district_data = sdf[(sdf['Area name'] == district)& (sdf['Total/Rural/Urban'] == area_type) ]
    fig_json_total=bar_chart(district_data,'person',district,area_type)
    fig_json_males=bar_chart(district_data,'males',district,area_type)
    fig_json_females=bar_chart(district_data,'females',district,area_type)

    male_count = district_data[district_data["Education level"]=="Total"]["total males"].iloc[0]
    female_count = district_data[district_data["Education level"]=="Total"]["total females"].iloc[0]
    gender_pie_json=draw_pie_chart(male_count,female_count)

    data_dict={
        'fig_json':fig_json_total,
        'fig_json_males':fig_json_males,
        'fig_json_females':fig_json_females,
        'gender_pie_json':gender_pie_json,
        'district':district
    }
    return render_template('visualization_dist.html', data=data_dict)

if __name__ == "__main__":
    app.run(debug=True)
