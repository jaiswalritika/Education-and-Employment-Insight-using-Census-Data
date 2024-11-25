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

def gender_gap_chart(dataset, region, area_type):
    fig = go.Figure()
    if not dataset.empty:
        male_employment = ((dataset['males main worker'].astype(float) + dataset['males marginal worker'].astype(float)) / dataset['total males'].astype(float)) * 100
        female_employment = ((dataset['females main worker'].astype(float) + dataset['females marginal worker'].astype(float)) / dataset['total females'].astype(float)) * 100
        gap = male_employment - female_employment
        
        fig.add_trace(go.Bar(
            x=dataset['Education level'],
            y=gap,
            name='Gender Gap',
            marker_color=['red' if x > 0 else 'green' for x in gap]
        ))
        
        fig.update_layout(
            title=f'Gender Gap in Employment - {region} ({area_type})',
            xaxis_title='Education Level',
            yaxis_title='Employment Gap (Male % - Female %)',
            width=1200,
            height=500,
            showlegend=False
        )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def worker_distribution_chart(dataset, region, area_type):
    fig = go.Figure()
    if not dataset.empty:
        main_workers = dataset['person main worker'].astype(float)
        marginal_workers = dataset['person marginal worker'].astype(float)
        unemployed = dataset['person unemployed'].astype(float)
        maw = dataset['person MAW'].astype(float)
        
        fig.add_trace(go.Bar(x=dataset['Education level'], y=main_workers, name='Main Workers'))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=marginal_workers, name='Marginal Workers'))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=unemployed, name='Unemployed'))
        fig.add_trace(go.Bar(x=dataset['Education level'], y=maw, name='MAW'))
        
        fig.update_layout(
            barmode='stack',
            title=f'Worker Distribution by Education Level - {region} ({area_type})',
            xaxis_title='Education Level',
            yaxis_title='Number of People',
            width=1200,
            height=500
        )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def employment_trend_chart(dataset, region, area_type):
    fig = go.Figure()
    if not dataset.empty:
        education_levels = dataset['Education level']
        employment_rate = ((dataset['person main worker'].astype(float) + dataset['person marginal worker'].astype(float)) / dataset['total person'].astype(float)) * 100
        
        fig.add_trace(go.Scatter(
            x=education_levels,
            y=employment_rate,
            mode='lines+markers',
            name='Employment Rate'
        ))
        
        fig.update_layout(
            title=f'Employment Rate Trend by Education Level - {region} ({area_type})',
            xaxis_title='Education Level',
            yaxis_title='Employment Rate (%)',
            width=1200,
            height=500
        )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def worker_type_pie(dataset):
    total_main = dataset['person main worker'].astype(float).sum()
    total_marginal = dataset['person marginal worker'].astype(float).sum()
    total_unemployed = dataset['person unemployed'].astype(float).sum()
    total_maw = dataset['person MAW'].astype(float).sum()
    total_non_worker = dataset['person non worker'].astype(float).sum()
    
    values = [total_main, total_marginal, total_unemployed, total_maw, total_non_worker]
    labels = ['Main Workers', 'Marginal Workers', 'Unemployed', 'MAW', 'Non Workers']
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(
        title='Distribution of Worker Types',
        width=800,
        height=600
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def gender_participation_ratio(dataset):
    fig = go.Figure()
    education_levels = dataset['Education level']
    
    male_ratio = (dataset['males main worker'].astype(float) + dataset['males marginal worker'].astype(float)) / dataset['total males'].astype(float) * 100
    female_ratio = (dataset['females main worker'].astype(float) + dataset['females marginal worker'].astype(float)) / dataset['total females'].astype(float) * 100
    
    fig.add_trace(go.Bar(name='Male Participation', x=education_levels, y=male_ratio))
    fig.add_trace(go.Bar(name='Female Participation', x=education_levels, y=female_ratio))
    
    fig.update_layout(
        barmode='relative',
        title='Gender-wise Workforce Participation by Education Level',
        xaxis_title='Education Level',
        yaxis_title='Participation Rate (%)',
        width=1200,
        height=600
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def education_impact_scatter(dataset):
    fig = px.scatter(dataset, 
        x='Education level',
        y=((dataset['person main worker'].astype(float) + dataset['person marginal worker'].astype(float)) / dataset['total person'].astype(float) * 100),
        size=dataset['total person'].astype(float),
        color=((dataset['person unemployed'].astype(float) + dataset['person MAW'].astype(float)) / dataset['total person'].astype(float) * 100),
        labels={
            'y': 'Employment Rate (%)',
            'color': 'Unemployment Rate (%)'
        },
        title='Education Impact on Employment (Size: Total Population)',
        color_continuous_scale=['rgb(25,25,112)', 'rgb(65,105,225)', 'rgb(100,149,237)']  # Dark blue color scheme
    )
    
    fig.update_layout(
        width=1200, 
        height=600,
        paper_bgcolor='white',
        plot_bgcolor='white',
        title={
            'font': {'size': 24, 'color': 'black'},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis={'gridcolor': 'lightgray', 'gridwidth': 1},
        yaxis={'gridcolor': 'lightgray', 'gridwidth': 1}
    )
    
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='rgb(50,50,50)'),
            opacity=0.7
        )
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/visualize', methods=['POST'])
def visualize():
    state = request.form.get('state')
    area_type = request.form.get('area_type')
    
    # Visualization code
    state_data = df[(df['Area name'] == state) & (df['Total/Rural/Urban'] == area_type)]
    fig_json_total = bar_chart(state_data,'person',state,area_type)
    fig_json_males = bar_chart(state_data,'males',state,area_type)
    fig_json_females = bar_chart(state_data,'females',state,area_type)
    gender_gap = gender_gap_chart(state_data, state, area_type)
    worker_dist = worker_distribution_chart(state_data, state, area_type)
    emp_trend = employment_trend_chart(state_data, state, area_type)
    worker_type_pie_chart = worker_type_pie(state_data)
    gender_participation = gender_participation_ratio(state_data)
    education_impact = education_impact_scatter(state_data)

    global sdf
    sdf = pd.read_csv('data/states_data/'+state.title()+".csv")
    districts = sdf['Area name'].unique()
    dist_area_types = sdf['Total/Rural/Urban'].unique()
    
    data_dict = {
        'fig_json': fig_json_total,
        'fig_json_males': fig_json_males,
        'fig_json_females': fig_json_females,
        'gender_gap': gender_gap,
        'worker_dist': worker_dist,
        'emp_trend': emp_trend,
        'worker_type_pie': worker_type_pie_chart,
        'gender_participation': gender_participation,
        'education_impact': education_impact,
        'state': state,
        'district': districts,
        'dist_area_types': dist_area_types
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
