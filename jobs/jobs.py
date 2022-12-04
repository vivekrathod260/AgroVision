from django.contrib.auth.models import User
from Home.models import USER
import time
from datetime import datetime, timedelta
import requests
import json
import os
from django.core.serializers import serialize
# utils python functions
from Home.utils.geojsonfun import GEOJSON
# email
from django.conf import settings
from django.core.mail import send_mail
# template email
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

def SendWeatherForcast():
    print('''****************************** HELLO TIME : '''+datetime.now().strftime("%H-%M-%S")+"****************************")
    date_start = "20" + (datetime.now() + timedelta(days=2,hours=0)).strftime("%y-%m-%d")
    date_end = "20" + (datetime.now() + timedelta(days=3,hours=0)).strftime("%y-%m-%d")

    au = USER.objects.all()
    au1 = serialize("json", au)
    AllUSER = json.loads(au1)
    print(len(AllUSER))
    # for queryObj in AllUSER:
    for i in range(0,len(AllUSER)-1):
        queryObj = AllUSER[i]
        dictionary = queryObj["fields"]
        data = dictionary["fields"]
        currentUser = dictionary["username"]
        if data != "[]":
            fieldList = json.loads(data)
            # for field in fieldList:
            for j in range(0,len(fieldList)-1):
                field = fieldList[j]
                fieldID = field["fieldId"]
                cropType = field["cropType"]
                area = field["area"]
                coordinates = json.dumps(field["coord"])
                geojson = GEOJSON(field["cropType"],field["sowingDate"] ,field["year"] ,coordinates)
                # print(geojson)

                url1 = "https://api-connect.eos.com/field-management"
                payload1 = geojson
                headers = {
                    "x-api-key" : settings.API_KEY
                }
                response1 = requests.request("POST", url1, headers=headers, data=payload1)
                # print(response1.text)
                if response1.status_code != 201:
                    print("Status code:"+str(response1.status_code)+" Response:"+response1.text)
                    break
                dict1 = json.loads(response1.text)
                fieldIdNo = dict1["id"]

                urlW = "https://api-connect.eos.com/weather/forecast/"+str(fieldIdNo)
                v1 = '{"params":{"date_start":"'
                v2 = '","date_end":"'
                v3 = '"},"provider":"icon"}'
                dateWS = date_start
                dateWE = date_end
                payloadW = v1 + dateWS + v2 + dateWE + v3
                # print(payloadW)
                responseW = requests.request("POST", urlW, headers=headers, data=payloadW)
                # print(responseW.text)
                if responseW.status_code != 200:
                    print("Status code:"+str(responseW.status_code)+" Response:"+responseW.text)
                    break
                listW = json.loads(responseW.text)
                d2 = listW[0]
                # print(tomorrowW)
                tomorrowWDate = d2["date"]
                d3 = listW[1]
                wind1 = str(d2["forecast"][4].get("wind"))[0:4]
                humidity1 = d2["forecast"][4].get("humidity")
                temp1 = d2["forecast"][4].get("temperature_max")
                cloud1 = d2["forecast"][4].get("cloudiness")

                # sending email
                subject = "Weather Forcast"
                message = f"Date:{tomorrowWDate} Wind = {wind1}, Humidity = {humidity1}, Temperature = {temp1}, Cloud = {cloud1}"
                email_from = settings.EMAIL_HOST_USER

                email = json.loads(serialize("json", User.objects.filter(username=field["username"])))[0]["fields"].get("email")
                recipient_list = [email]

                plaintext = get_template('mail_body.txt')
                htmly     = get_template('mail_body.html')

                d = {
                    'fieldId':fieldID,
                    'area': area,
                    'cropType' : cropType,
                    'Date': tomorrowWDate,
                    'Wind': wind1,
                    'Humidity':humidity1,
                    'Temperature':temp1,
                    'Cloud':cloud1
                }
                
                text_content = plaintext.render(d)
                html_content = htmly.render(d)
                msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
                print("Email send to "+currentUser)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
        else:
            print("No field ... so no email to "+ currentUser)
            continue
            # Dont send message to this user email
    print("####################### Ideal ###############################")