import json

with open('sample-stocks-data.json','r') as json_file:
    data = json.load(json_file)

target = 'AMZN'
company_data=[]
for item in data:
    if item["symbol"] == "AMZN" :
        company_data.append(item)

print(company_data)