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
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']

    if selected_cmu != 'All':
        ncasdf = ncasdf[ncasdf['CMU'] == selected_cmu]

    if selected_country != 'All':
        ncasdf = ncasdf[ncasdf['Country'] == selected_country]
        selected_cmu = ncasdf['CMU'].unique()[0]

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

    english_documents = str(ncasdf[ncasdf['Language']=='English']['Document Title'].count())
    perc_english = str(round(ncasdf[ncasdf['Language']=='English']['Document Title'].count()*100/ncasdf['Document Title'].count()))


    sector_specific = ncasdf[ncasdf['Policy type'] == 'Sector-specific']
    sector_specific['Document date'] = pd.to_datetime(sector_specific['Document date'])
    sector_specific['Document Year'] = sector_specific['Document date'].dt.year
    # Group by and get the max year
    sector_specific_grouped = sector_specific.groupby(['CMU', 'Country', 'Category'])['Document Year'].max().reset_index()
    sector_specific_grouped['Document Year'] = sector_specific_grouped['Document Year'].fillna(0).astype(int).astype(str)
    # Merge with original data to retain the Status
    merged_df = pd.merge(sector_specific_grouped, ncasdf, on=['CMU', 'Country', 'Category'], how='left')
    # Pivot the DataFrame
    pivot_df = merged_df.pivot_table(index=["CMU", "Country"], 
                                     columns="Category", values="Document Year", aggfunc='first')
    # Fill NaN values with 'Not Available'
    pivot_df.fillna('Not Available', inplace=True)
    # Replace '0' with the corresponding Status
    for index, row in pivot_df.iterrows():
        for col in pivot_df.columns:
            if row[col] == '0':
                status = merged_df[(merged_df['CMU'] == index[0]) & 
                                   (merged_df['Country'] == index[1]) & 
                                   (merged_df['Category'] == col)]['Status'].values[0]
                pivot_df.at[index, col] = status
    sector_df_dict = pivot_df.reset_index()
    sector_df_dict['CMU'] = sector_df_dict['CMU'].apply(lambda x:x.replace('_',' '))
    sector_columns = sector_df_dict.columns


    law_legis = ncasdf[ncasdf['Policy type'] == 'Law/Legislation']
    law_legis['Document date'] = pd.to_datetime(law_legis['Document date'])
    law_legis['Document Year'] = law_legis['Document date'].dt.year
    # Group by and get the max year
    law_legis_grouped = law_legis.groupby(['CMU', 'Country', 'Category'])['Document Year'].max().reset_index()
    law_legis_grouped['Document Year'] = law_legis_grouped['Document Year'].fillna(0).astype(int).astype(str)
    # Merge with original data to retain the Status
    merged_df = pd.merge(law_legis_grouped, ncasdf, on=['CMU', 'Country', 'Category'], how='left')
    # Pivot the DataFrame
    pivot_df = merged_df.pivot_table(index=["CMU", "Country"], 
                                     columns="Category", values="Document Year", aggfunc='first')
    # Fill NaN values with 'Not Available'
    pivot_df.fillna('Not Available', inplace=True)
    # Replace '0' with the corresponding Status
    for index, row in pivot_df.iterrows():
        for col in pivot_df.columns:
            if row[col] == '0':
                status = merged_df[(merged_df['CMU'] == index[0]) & 
                                   (merged_df['Country'] == index[1]) & 
                                   (merged_df['Category'] == col)]['Status'].values[0]
                pivot_df.at[index, col] = status
    law_legis_df_dict = pivot_df.reset_index()
    law_legis_df_dict['CMU'] = law_legis_df_dict['CMU'].apply(lambda x:x.replace('_',' '))
    law_legis_columns = law_legis_df_dict.columns

    return render_template(
        'dashboard.html', 
        country_counts=count_df.to_dict(orient='records'),
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
        law_legis_df_dict = law_legis_df_dict,law_legis_columns = law_legis_columns
    )

@app.route('/index')
def index():
    ncasdf = pd.read_excel('database.xlsx')
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']

    color_status_dict = {'Adopted':'green','Draft':'yellow','Work in Progress':'orange','Unknown':'red'}
    ncasdf['Status'].fillna('Unknown',inplace=True)
    ncasdf['color_status'] = ncasdf['Status'].apply(lambda x: color_status_dict[x])
    
    ncasdf['Language'].fillna('N/A',inplace=True)
    color_language_dict = {'English':'blue','Non-English':'violet','N/A':'red'}
    ncasdf['color_language'] = ncasdf['Language'].apply(lambda x: color_language_dict[x])
    ncasdf['Language_2'] = ncasdf['Language_2'].fillna(ncasdf['Language'])

    ncasdf['Document date'] = ncasdf['Document date'].apply(lambda x:str(x)[0:10])

    color_access_dict = {'Public':'#013220','Restricted Use':'Coral','N/A':'red'}
    ncasdf['Accessibility'].fillna('N/A',inplace=True)
    ncasdf['color_access'] = ncasdf['Accessibility'].apply(lambda x: color_access_dict[x])

    for idx, col in enumerate(ncasdf.columns):
        print(f"Column ID: {idx}, Column Name: {col}, First Value: {ncasdf[col].iloc[0]}")

    return render_template('index.html',row_data=list(ncasdf.astype(str).values.tolist()))

@app.route('/record',methods=['POST'])
def record():
    if request.method == 'POST':
        ncasdf = pd.read_excel('database.xlsx')

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
    ncasdf = pd.read_excel('database.xlsx')
    ncasdf = ncasdf[ncasdf['CMU'].astype(str)!='nan']

    cmu_list = list(ncasdf['CMU'].unique())
    country_list = list(ncasdf['Country'].unqique())
    policy_type = list(ncasdf['Policy type'].unqique())
    category_type = list(ncasdf['Category'].unique())

    return render_template('record.html',
        button_text='Update Database', form_type='main_route',
        cmu_list=cmu_list,country_list=country_list,
        policy_type=policy_type,category_type=category_type)

@app.route('/genai')
def recommendations():
    return render_template('recommendations.html')


if __name__ == "__main__":
   app.run(debug=True,port=8080)




