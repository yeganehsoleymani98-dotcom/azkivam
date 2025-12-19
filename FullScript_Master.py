import os
import pandas as pd
import numpy as np
import pyodbc
from datetime import datetime, timedelta
import json
#from Functions import return_jalali_date, user_pyodbc_connection, pyodbc_connection
#from Functions import Node1va2_Username, Node1va2_Password
from Functions import *
import jdatetime
from datetime import timedelta
import jdatetime
import requests
from datetime import timedelta, datetime
from persiantools.jdatetime import JalaliDate
import re
from dotenv import load_dotenv



from openai import OpenAI

client = OpenAI(
    api_key="local-api-key",   # هرچیزی، مهم نیست
    base_url="http://127.0.0.1:1234/v1"
)



def classify_item(text: str) -> str:
    response = client.chat.completions.create(
        
        model="qwen3-4b-instruct-2507",  # مثلا: mistral, llama3, qwen
        temperature=0,
        messages=[
            {"role": "user", "content": text}]
    )
    return response.choices[0].message.content.strip()


ScrapingData = pd.read_excel('sample2.xlsx')


ScrapingGroups = []

for i in  ScrapingData.biography:
    ScrapingGroups.append(classify_item(i))
    
    
pd.DataFrame(ScrapingGroups , columns = ['Master'])

ScrapingData['Master'] = pd.DataFrame(ScrapingGroups)


ScrapingData['FlwingRate'] = 0.8*(ScrapingData['followers']/ScrapingData['following']) + (0.2*ScrapingData['posts']) - 2
ScrapingData['FlwingRate_raw'] = (
    0.8 * (ScrapingData['followers'] / ScrapingData['following']) +
    0.2 * ScrapingData['posts'] - 2
)


min_val = ScrapingData['FlwingRate_raw'].min()
max_val = ScrapingData['FlwingRate_raw'].max()

ScrapingData['FlwingRate'] = 1 + 4 * (
    (ScrapingData['FlwingRate_raw'] - min_val) / (max_val - min_val)
)

DBData = pd.read_excel('Keywords_Merch.xlsx')

DBGroups = []

for i in  DBData.Keywords:
    DBGroups.append(classify_item(i))
    
    
DBData['MerchMasterKey'] = pd.DataFrame(DBGroups)

DBData= DBData[['MerchMasterKey' , 'Id' , 'Score']]

dictNames = {
    'id' : 'Id',
    'FlwingRate' : 'Score',
    'MerchMasterKey' : 'Master'}

ScrapingData = ScrapingData[['id' , 'FlwingRate' , 'Master']]

DBData.rename(columns = dictNames , inplace = True)
ScrapingData.rename(columns = dictNames , inplace = True)

FinalData = pd.concat([DBData , ScrapingData] , axis = 0)
FinalData[FinalData['Master'] == 'طلا'].head(10).sort_values(by = 'Score' , ascending = False)

