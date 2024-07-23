from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import random
import string
from datetime import date
import folium
from folium.features import GeoJsonTooltip


app = Flask(__name__)

@app.route('/')
def dashboard():
    selected_cmu = request.args.get('CMU', 'All')
    selected_country = request.args.get('COUNTRY', 'All')

    country_to_code = {
    'Albania': 'ALB',
    'Armenia': 'ARM',
    'Azerbaijan': 'AZE',
    'Bosnia & Herzegovina': 'BIH',
    'Croatia': 'HRV',
    'Georgia': 'GEO',
    'Kazakhstan': 'KAZ',
    'Kosovo': 'XKX',
    'Kyrgyzstan': 'KGZ',
    'Moldova': 'MDA',
    'Montenegro': 'MNE',
    'North Macedonia': 'MKD',
    'Poland': 'POL',
    'Romania': 'ROU',
    'Serbia': 'SRB',
    'Tajikistan': 'TJK',
    'Turkiye': 'TUR',
    'Turkmenistan': 'TKM',
    'Ukraine': 'UKR',
    'Uzbekistan': 'UZB',
    'Austria':'AUT'
    }

    ncasdf = pd.read_excel('static/data/database.xlsx')
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']
    ncasdf['Document date'] = pd.to_datetime(ncasdf['Document date'])
    ncasdf['Document Year'] = ncasdf['Document date'].dt.year
    ncasdf['Document Year'] = ncasdf['Document Year'].fillna(0).astype(int).astype(str)

    if selected_cmu != 'All':
        ncasdf = ncasdf[ncasdf['CMU'] == selected_cmu]

    if selected_country != 'All':
        ncasdf = ncasdf[ncasdf['Country'] == selected_country]
        selected_cmu = ncasdf['CMU'].unique()[0]

    table_df = ncasdf.copy()
    count_df = table_df.groupby(['Country'])['Document Title'].count().reset_index()
    count_df['Country_Code'] = count_df['Country'].apply(lambda x: country_to_code[x])

    policy_type_count = table_df.groupby(['Policy type'])['Document Title'].count().reset_index()

    cmu_list = ncasdf['CMU'].unique().tolist()
    cmu_list.sort()

    country_list = ncasdf['Country'].unique().tolist()
    country_list.sort()

    cmu_list.insert(0, 'All')
    country_list.insert(0, 'All')

    english_documents = str(ncasdf[ncasdf['Language']=='English']['Document Title'].count())
    perc_english = str(round(ncasdf[ncasdf['Language']=='English']['Document Title'].count()*100/ncasdf['Document Title'].count()))

    def get_dict(df):
        # Group by and get the max year
        df_grouped = df.groupby(['CMU', 'Country', 'Short Title'])['Document Year'].max().reset_index()
        # Merge with original data to retain the Status
        merged_df = pd.merge(df_grouped, ncasdf, on=['CMU', 'Country', 'Short Title','Document Year'], how='left')
        # Pivot the DataFrame
        pivot_df = merged_df.pivot_table(index=["CMU", "Country"], 
                                         columns="Short Title", values="Document Year", aggfunc='first')
        # Fill NaN values with 'Not Available'
        pivot_df.fillna('Not Available', inplace=True)
        
        test = pivot_df.reset_index()

        # Replace '0' with the corresponding Status
        for index, row in pivot_df.iterrows():
            for col in pivot_df.columns:
                if row[col] == '0':
                    status = merged_df[(merged_df['CMU'] == index[0]) & 
                                       (merged_df['Country'] == index[1]) & 
                                       (merged_df['Short Title'] == col)]['Status'].values[0]
                    pivot_df.at[index, col] = status

        # Replace further NaN values with the corresponding Accessibility
        for index, row in pivot_df.iterrows():
            for col in pivot_df.columns:
                if str(row[col]) == 'nan':
                    accessibility = merged_df[(merged_df['CMU'] == index[0]) & 
                                       (merged_df['Country'] == index[1]) & 
                                       (merged_df['Short Title'] == col)]['Accessibility'].values[0]
                    pivot_df.at[index, col] = accessibility

        df_dict = pivot_df.reset_index()
        df_dict['CMU'] = df_dict['CMU'].apply(lambda x:x.replace('_',' '))
        return df_dict

    # Sector Summaries
    sector_specific = ncasdf[ncasdf['Policy type'] == 'Sector-specific strategy']
    sector_df_dict = get_dict(sector_specific)
    sector_columns = sector_df_dict.columns

    #Law/Legislation Summary
    law_legis = ncasdf[ncasdf['Policy type'] == 'Law/Legislation']
    law_legis_df_dict = get_dict(law_legis)
    law_legis_columns = law_legis_df_dict.columns

    #National Strategy Summary
    national_strategy = ncasdf[ncasdf['Policy type'] == 'National strategy']
    national_strategy_dict = get_dict(national_strategy)
    national_strategy_columns = national_strategy_dict.columns

    columns_ordered = ['NDC','LTS', 'NECP', 
        'Climate Change Strategy','NAP','Energy Strategy','Climate change Law',
        'Air Protection Law','Energy Efficiency Law','Renewable Energy Law','CCDR']
    main_dashboard = ncasdf[ncasdf['Short Title'].isin(columns_ordered)]
    main_dashboard_dict = get_dict(main_dashboard)
    columns_ordered = list(set(columns_ordered).intersection(set(main_dashboard_dict.columns)))
    all_columns = ['CMU','Country']+columns_ordered
    main_dashboard_dict = main_dashboard_dict[all_columns]
    main_dashboard_columns = main_dashboard_dict.columns

    m = folium.Map(location=[50, 60], zoom_start=3, tiles='cartodbpositron')

    # Add the Choropleth layer
    choropleth = folium.Choropleth(
            geo_data='https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json',
            name='choropleth',
            data=count_df,
            columns=['Country', 'Document Title'],
            key_on='feature.properties.name',
            fill_color='YlGn',
            fill_opacity=1,
            line_opacity=0.5,
            legend_name=None
    )
    for key in choropleth._children:
        if key.startswith('color_map'):
            del(choropleth._children[key])
    choropleth.add_to(m)

    country_to_doc = dict(zip(count_df['Country'], count_df['Document Title']))

    # Modify GeoJSON data to include Document Title and set non-data countries to grey
    geojson_data = choropleth.geojson.data
    for feature in geojson_data['features']:
        country_name = feature['properties']['name']
        if country_name in country_to_doc:
            feature['properties']['document_title'] = country_to_doc[country_name]
        else:
            feature['properties']['document_title'] = 'N/A'
            feature['properties']['style'] = {'fillColor': '#D3D3D3', 'fillOpacity': 1, 'weight': 0}


    # Add hover functionality
    style_function = lambda x: x['properties']['style'] if 'style' in x['properties'] else {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}

    tooltip = GeoJsonTooltip(
        fields=['name', 'document_title'],
        aliases=['Country: ', 'Number of Documents: '],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    )


    # Add GeoJson layer with tooltip
    folium.GeoJson(
        geojson_data,
        style_function=style_function,
        control=False,
        tooltip=tooltip
    ).add_to(m)

    m.save('static/assets/folium_choropleth_map.html')

    return render_template(
        'dashboard.html',
        cmu_list=cmu_list,
        selected_cmu=selected_cmu,
        country_list=country_list,
        selected_country=selected_country,
        table_data=table_df.to_dict(orient='records'),
        total_docs = str(ncasdf['Document Title'].count()),
        policy_type_count = list(policy_type_count.values.tolist()),
        english_documents = english_documents,
        perc_english = perc_english,
        sector_df_dict = sector_df_dict,sector_columns = sector_columns,
        law_legis_df_dict = law_legis_df_dict,law_legis_columns = law_legis_columns,
        national_strategy_dict = national_strategy_dict, national_strategy_columns=national_strategy_columns,
        main_dashboard_dict = main_dashboard_dict, main_dashboard_columns=main_dashboard_columns
    )

@app.route('/index')
def index():
    ncasdf = pd.read_excel('static/data/database.xlsx')
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']

    color_status_dict = {'Adopted':'green','Draft':'#DAA520','Work in Progress':'orange','Unknown':'red'}
    ncasdf['Status'].fillna('Unknown',inplace=True)
    ncasdf['color_status'] = ncasdf['Status'].apply(lambda x: color_status_dict[x.strip()])
    
    ncasdf['Language'].fillna('N/A',inplace=True)
    color_language_dict = {'English':'blue','Non-English':'violet','N/A':'red'}
    ncasdf['color_language'] = ncasdf['Language'].apply(lambda x: color_language_dict[x.strip()])
    ncasdf['Language_2'] = ncasdf['Language_2'].fillna(ncasdf['Language'])

    ncasdf['Document date'] = ncasdf['Document date'].apply(lambda x:str(x)[0:10])

    color_access_dict = {'Public':'#013220','Restricted Use':'Coral','N/A':'red'}
    ncasdf['Accessibility'].fillna('N/A',inplace=True)
    ncasdf['color_access'] = ncasdf['Accessibility'].apply(lambda x: color_access_dict[x.strip()])

    ncasdf = ncasdf.fillna('No additional remarks')

    return render_template('index.html',row_data=list(ncasdf.astype(str).values.tolist()))

@app.route('/record',methods=['POST'])
def record():
    if request.method == 'POST':
        ncasdf = pd.read_excel('static/data/database.xlsx')

        cmu = request.form['CMU']
        country = request.form['Country']
        shortTitle = request.form['Short Title']
        docTitle = request.form['Document Title']
        pdfLink = request.form['PDF Link']
        language = request.form['Language']
        otherLanguageInput = request.form['otherLanguageInput']
        refLink = request.form['Reference Link']
        status = request.form['Status']
        policyType = request.form['Policy type']
        category = request.form['Category']
        documentDate = request.form['Document Date']
        comments = request.form['Comments']
        accessibility = request.form['accessibility']

        df_new_record = pd.DataFrame([[cmu,country,shortTitle,docTitle,
                    refLink,pdfLink,accessibility,language,otherLanguageInput,status,policyType,
                    category,documentDate,comments,None]])
        df_new_record.columns = ncasdf.columns

        ncasdf = pd.concat([ncasdf, df_new_record], ignore_index=True)
        ncasdf.to_excel('database.xlsx', index=False)
        
        return redirect(url_for('index'))

@app.route('/record', methods=['GET'])
def recordroute():
    ncasdf = pd.read_excel('static/data/database.xlsx')
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']

    cmu_list = list(ncasdf['CMU'].unique())
    country_list = list(ncasdf['Country'].unique())
    policy_type = list(ncasdf['Policy type'].unique())
    category_type = list(ncasdf['Category'].unique())

    return render_template('record.html',
        button_text='Update Database', form_type='main_route',
        cmu_list=cmu_list,country_list=country_list,
        policy_type=policy_type,category_type=category_type)

@app.route('/genai')
def recommendations():
    return render_template('recommendations.html')

@app.route('/about')
def about():
    df_country = pd.read_excel('static/data/acknowledgment.xlsx',sheet_name='Sheet1')
    df_dfc = pd.read_excel('static/data/acknowledgment.xlsx',sheet_name='Sheet2')

    return render_template('about.html',
        country_teams=list(df_country.astype(str).values.tolist()),
        dfc_teams=list(df_dfc.astype(str).values.tolist()))

if __name__ == "__main__":
   app.run()




