import json,time

def getFieldIndex(request,imageName,):
    queryObj = UserData.objects.filter(username = request.user.username)
    jsonObj = serialize("json", queryObj)
    arrOfDictObj = json.loads(jsonObj)
    userData = arrOfDictObj[0]["fields"]
    data = userData["fields"]
    if data == "[]":
        return HttpResponse("You don't have any field added .. please add a field first")
    fieldList = json.loads(data)
    targetField = {}
    for field in fieldList:
        if field["fieldId"]==fieldId:
            targetField = field
    coordinates = json.dumps(targetField["coord"])
    geojson = GEOJSON(targetField["cropType"],targetField["sowingDate"] ,targetField["year"] ,coordinates)
    print(geojson)
    url1 = "https://api-connect.eos.com/field-management"
    payload1 = geojson
    headers = {
        "x-api-key" : "apk.b4298ea53d7845b1d6d00b8d989b4e62190900bfe0c35eac84bea59add85bf84"
    }
    response1 = requests.request("POST", url1, headers=headers, data=payload1)
    print(response1.text)
    if response1.status_code != 201:
        return HttpResponse("Status code:"+str(response1.status_code)+" Response:"+response1.text)
    dict1 = json.loads(response1.text)
    fieldId = dict1["id"]

    
    url2 = "https://api-connect.eos.com/scene-search/for-field/"+str(fieldId)
    payload2 = '''{
    "params": {
        "date_start" : "2022-11-02",
        "date_end" : "2022-11-07",
        "data_source" : [
            "sentinel2"
        ]

    }
    }'''
    response2 = requests.request("POST", url2, headers=headers, data=payload2)
    print(response2.text)
    if response2.status_code != 201:
        return HttpResponse("Status code:"+str(response2.status_code)+" Response:"+response2.text)
    dict2 = json.loads(response2.text)
    reqId = dict2["request_id"]
    response2.close()


    url3 = "https://api-connect.eos.com/scene-search/for-field/"+str(fieldId)+"/"+str(reqId)
    payload3 = ""
    time.sleep(12)
    response3 = requests.request("GET", url3, headers=headers, data=payload3)
    if response3.status_code != 200:
        return HttpResponse("Status code:"+str(response3.status_code)+" Response:"+response3.text)
    print(response3.text) 
    dict3 = json.loads(response3.text)
    resultListOfDict = dict3["result"]
    i = len(resultListOfDict)-1
    viewId = resultListOfDict[i]["view_id"]
    while i!=-1:
        if resultListOfDict[i]["cloud"]==0.0:
            viewId = resultListOfDict[i]["view_id"]
            break
        i = i-1

    
    url4 = "https://api-connect.eos.com/field-imagery/indicies/"+str(fieldId)
    payload4 = '''{
        "params": {
            "view_id": "S2/43/Q/HC/2022/11/4/0",
            "index": "NDVI",
            "format": "png"
        },
        "callback_url": "https://test.local"
    }'''
    p4Dict = json.loads(payload4)
    p4Dict["params"]["view_id"] = viewId
    payload4 = json.dumps(p4Dict)
    time.sleep(0)
    response4 = requests.request("POST", url4, headers=headers, data=payload4)
    if response4.status_code != 202:
        return HttpResponse("Status code:"+str(response4.status_code)+" Response:"+response4.text)
    print(response4.text)
    dict4 = json.loads(response4.text)
    requestId = dict4["request_id"]


    url5 = "https://api-connect.eos.com/field-imagery/"+str(fieldId)+"/"+str(requestId)
    payload5 = ""
    time.sleep(8)
    response5 = requests.request("GET", url5, headers=headers, data=payload5)
    if response5.status_code != 200:
        return HttpResponse("Status code:"+str(response5.status_code)+" Response:"+response5.text)

    open(str(os.getcwd())+"\\static\\fieldimages\\image.png", 'wb').write(response5.content)
    time.sleep(8)
    return render(request,"#image.html")