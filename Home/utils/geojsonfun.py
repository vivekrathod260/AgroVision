import json
def GEOJSON(cropType,sowingDate,year,coord):
    s1 = '{"type":"Feature","properties":{"name":"valid","group":null,"years_data":[{"crop_type":"'
    s2 = '","year":'
    s3 = ',"sowing_date":"'
    s4 = '"}]},"geometry":{"type":"Polygon","coordinates":'
    s5 = '}}'
    geojson = s1+cropType+s2+year+s3+sowingDate+s4+coord+s5
    return geojson





