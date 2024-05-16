from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import random
import string
from datetime import date

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
    'Uzbekistan': 'UZB'
    }

    ncasdf = pd.read_excel('database.xlsx')

    if selected_cmu != 'All':
        ncasdf = ncasdf[ncasdf['CMU'] == selected_cmu]

    if selected_country != 'All':
        ncasdf = ncasdf[ncasdf['Country'] == selected_country]

    table_df = ncasdf.copy()
    count_df = table_df.groupby(['Country'])['Document Title'].count().reset_index()
    count_df['Country_Code'] = count_df['Country'].apply(lambda x: country_to_code[x])

    policy_type_count = table_df.groupby(['Policy type'])['Document Title'].count().reset_index()
    policy_type_count['policy type'] = policy_type_count['Policy type'].apply(lambda x:x.replace('/',' and '))

    cmu_list = ncasdf['CMU'].unique().tolist()
    cmu_list.sort()

    country_list = ncasdf['Country'].unique().tolist()
    country_list.sort()

    cmu_list.insert(0, 'All')
    country_list.insert(0, 'All')

    return render_template(
        'dashboard.html', 
        country_counts=count_df.to_dict(orient='records'),
        cmu_list=cmu_list,
        selected_cmu=selected_cmu,
        country_list=country_list,
        selected_country=selected_country,
        table_data=table_df.to_dict(orient='records'),
        total_docs = str(ncasdf['Document Title'].count()),
        policy_type_count=list(policy_type_count.values.tolist())
    )

@app.route('/index')
def index():
    ncasdf = pd.read_excel('database.xlsx')
    color_status_dict = {'Adopted':'green','Draft':'yellow','Work in Progress':'orange'}
    ncasdf['color_status'] = ncasdf['Status'].apply(lambda x: color_status_dict[x])
    color_language_dict = {'English':'purple','Non-English':'violet'}
    ncasdf['color_language'] = ncasdf['Language'].apply(lambda x: color_language_dict[x])
    ncasdf['Document date'] = ncasdf['Document date'].apply(lambda x:str(x)[0:10])

    return render_template('index.html',row_data=list(ncasdf.astype(str).values.tolist()))

@app.route('/record',methods=['POST'])
def record():
    if request.method == 'POST':
        ncasdf = pd.read_excel('database.xlsx')
        length_df = len(ncasdf)
        cmu = request.form['CMU']
        country = request.form['Country']
        shortTitle = request.form['Short Title']
        docTitle = request.form['Document Title']
        pdfLink = request.form['PDF Link']
        language = request.form['Language']
        refLink = request.form['Reference Link']
        status = request.form['Status']
        policyType = request.form['Policy type']
        category = request.form['Category']
        documentDate = request.form['Document Date']
        reviewDate = request.form['Review Date']
        comments = request.form['Comments']

        df_new_record = pd.DataFrame([[length_df,cmu,country,shortTitle,docTitle,
                    refLink,pdfLink,language,status,policyType,
                    category,documentDate,comments,reviewDate]])
        df_new_record.columns = ncasdf.columns

        ncasdf = pd.concat([ncasdf, df_new_record], ignore_index=True)
        ncasdf.to_excel('database.xlsx', index=False)
        
        return redirect(url_for('index'))

@app.route('/record', methods=['GET'])
def recordroute():
    cmu_list = ['Western Balkans', 'South Caucasus', 'Central Asia', 'Turkiye',
       'Eastern Europe', 'European Union']

    country_list = ['Albania', 'Bosnia & Herzegovina', 'Kosovo', 'Montenegro',
       'North Macedonia', 'Serbia', 'Azerbaijan', 'Armenia', 'Georgia',
       'Kazakhstan', 'Kyrgyzstan', 'Tajikistan', 'Turkmenistan',
       'Uzbekistan', 'Turkiye', 'Moldova', 'Ukraine', 'Croatia', 'Poland',
       'Romania']

    policy_type = [None, 'Law/Legislation', 'National strategy/program', 'Sector-specific','Action Plan']

    category_type = [None, 'Climate change', 'Energy', 'Air quality', 'Environment',
       'EU-specific', 'World Bank-specific', 'Industry', 'Transport ',
       'Agriculture', 'Waste', 'Urban', 'Rural', 'Water', 'Forestry',
       'Biodiversity', 'Other Energy Technologies']

    return render_template('record.html',
        button_text='Update Database', form_type='main_route',
        cmu_list=cmu_list,country_list=country_list,
        policy_type=policy_type,category_type=category_type)


if __name__ == "__main__":
   app.run(debug=True,port=8080)




