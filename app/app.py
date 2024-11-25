from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.graph_objs as go
import plotly.express as px

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

def bar_chart(dataset,params,region,area_type):
    fig = go.Figure()
    total_pop = dataset[dataset['Education level'] == 'Total']['total person'].values[0]
    total_pop_list = [total_pop] * dataset.shape[0]
    if not dataset.empty:
        total_persons=dataset['total '+params].astype(float)
        total_employed = ((dataset[params+' main worker'].astype(float) + dataset[params+' marginal worker'].astype(float))/total_persons)*100
        total_unemmployed = ((dataset[params+' unemployed'].astype(float) + dataset[params+' MAW'].astype(float))/total_persons)*100
        fig.add_trace(go.Bar(x=dataset['Education level'], y=(total_persons/total_pop_list)*100, name='Total %', width=0.25))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=total_unemmployed, name='Unemployed %', width=0.25))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=total_employed, name='Employed %', width=0.25))
        
        fig.update_layout(
            barmode='group',
            title={
                'text': f'{region} ({area_type}) {params} Education and Workforce Data',
                'y':0.95,
                'x':0.5,
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

@app.route('/visualize', methods=['POST'])
def visualize():
    state = request.form.get('state')
    area_type = request.form.get('area_type')
    state_data = df[(df['Area name'] == state) & (df['Total/Rural/Urban'] == area_type)]
    fig_json_total=bar_chart(state_data,'person',state,area_type)
    fig_json_males=bar_chart(state_data,'males',state,area_type)
    fig_json_females=bar_chart(state_data,'females',state,area_type)

    global sdf
    sdf=pd.read_csv('data/states_data/'+state.title()+".csv")
    districts = sdf['Area name'].unique()
    dist_area_types = sdf['Total/Rural/Urban'].unique()
    data_dict={
        'fig_json':fig_json_total,
        'fig_json_males':fig_json_males,
        'fig_json_females':fig_json_females,
        'state':state,
        'district':districts,
        'dist_area_types':dist_area_types
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
    data_dict={
        'fig_json':fig_json_total,
        'fig_json_males':fig_json_males,
        'fig_json_females':fig_json_females,
        'district':district
    }
    return render_template('visualization_dist.html', data=data_dict)

if __name__ == "__main__":
    app.run(debug=True)
