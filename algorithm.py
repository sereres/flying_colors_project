import time
import pickle
import datetime
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import pandas as pd
import csv
import matplotlib
from fbprophet import Prophet
from password import get_postgress_password

pk1_file = open('IllinoisDragonflies.pk1','rb')
illinoisDragonflies = pickle.load(pk1_file)
print(len(illinoisDragonflies))

pk2_file = open('IllinoisMonarch.pk1','rb')
illinoisMonarch = pickle.load(pk2_file)
print(len(illinoisMonarch))

username = 'postgres'
password = get_postgress_password
host = 'localhost'
port = '5432'
db_name = 'observations'

engine = create_engine( 'postgresql://{}:{}@{}:{}/{}'.format(username, password, host, port, db_name) )
print(engine.url)

if not database_exists(engine.url):
    create_database(engine.url)
print(database_exists(engine.url))

with open('observations_formatted.csv',mode='w') as observationfile:
    data_writer = csv.writer(observationfile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
    data_writer.writerow(['entry','date','lattitude','longitude','butterfly_id','dragonfly_id'])
    for i in range(len(illinoisDragonflies)):
        time_is = '2000-01-01'
        location_is = '0,0'
        location_is_data = illinoisDragonflies[i]['location']
        time_is_data = illinoisDragonflies[i]['observed_on']
        if time_is_data:
            time_is = time_is_data
        if location_is_data:
            location_is = location_is_data
        location_split = tuple(float(x) for x in location_is.split(','))            
        taxon_ident = illinoisDragonflies[i]['taxon']['min_species_ancestry']
        taxon_ident_split = taxon_ident.split(',')
        s='_'
        s=s.join(taxon_ident_split)
        butterfly_is = 0
        dragonfly_is = 0
        for j in range(len(taxon_ident_split)):
            if int(taxon_ident_split[j])==47224:
                butterfly_is = s
            if int(taxon_ident_split[j])==47792:
                dragonfly_is = s
        data_writer.writerow([i,time_is,location_split[0],location_split[1],butterfly_is,dragonfly_is])
    for i in range(len(illinoisMonarch)):
        time_is = '2000-01-01'
        location_is = '0,0'
        location_is_data = illinoisMonarch[i]['location']
        time_is_data = illinoisMonarch[i]['observed_on']
        if time_is_data:
            time_is = time_is_data
        if location_is_data:
            location_is = location_is_data
        location_split = tuple(float(x) for x in location_is.split(','))            
        taxon_ident = illinoisMonarch[i]['taxon']['min_species_ancestry']
        taxon_ident_split = taxon_ident.split(',')
        s='_'
        s=s.join(taxon_ident_split)
        butterfly_is = 0
        dragonfly_is = 0
        for j in range(len(taxon_ident_split)):
            if int(taxon_ident_split[j])==47224:
                butterfly_is = s
            if int(taxon_ident_split[j])==47792:
                dragonfly_is = s
        data_writer.writerow([i,time_is,location_split[0],location_split[1],butterfly_is,dragonfly_is])  

flying_color_data = pd.read_csv('observations_formatted.csv', index_col =0)
flying_color_data.to_sql('observations_table', engine, if_exists='replace')
con = None
con = psycopg2.connect(database = db_name, user = username)

sql_query_dragonfly = """
select date, count(*) from observations_table where butterfly_id='0' group by date order by date
"""
dragonfly_data_from_sql = pd.read_sql_query(sql_query_dragonfly,con)
print(dragonfly_data_from_sql)

sql_query_butterfly = """
select date, count(*) from observations_table where dragonfly_id='0' group by date order by date
"""
butterfly_data_from_sql = pd.read_sql_query(sql_query_butterfly,con)
print(butterfly_data_from_sql)

butterfly_data_from_sql.plot(x='date',y='count').get_figure().savefig('butterfly.png')
butterfly_model = Prophet()
butterfly_model.fit(butterfly_data_from_sql.rename(columns={'date':'ds','count':'y'}))

buterflyfuture = butterfly_model.make_future_dataframe(periods=365)    
butterfly_forecast = butterfly_model.predict(buterflyfuture)    

dragonfly_data_from_sql.plot(x='date',y='count').get_figure().savefig('dragonfly.png')
dragonfly_model = Prophet()
dragonfly_model.fit(dragonfly_data_from_sql.rename(columns={'date':'ds','count':'y'}))

dragonflyfuture = dragonfly_model.make_future_dataframe(periods=365)        
dragonfly_forecast = dragonfly_model.predict(dragonflyfuture)

with open('dragonfly_model.pck1','wb') as fout:
    pickle.dump(dragonfly_model,fout)

with open('butterfly_model.pck1','wb') as fout:
    pickle.dump(butterfly_model,fout)

with open('dragonfly_forecast.pck1','wb') as fout:
    pickle.dump(dragonfly_forecast,fout)

with open('butterfly_forecast.pck1','wb') as fout:
    pickle.dump(butterfly_forecast,fout)

butterfly_variable = 0
for i in butterfly_forecast.loc[butterfly_forecast['ds']== '2019-10-14']['yhat']:
    butterfly_variable = i
    print(i)
print(butterfly_variable)

dragonfly_variable = 0
for i in dragonfly_forecast.loc[dragonfly_forecast['ds']== '2019-10-14']['yhat']:
    dragonfly_variable = i
    print(i)
print(dragonfly_variable)

if butterfly_variable > dragonfly_variable:
    print("go see butterflies")
else:
    print("go see dragonflies")

