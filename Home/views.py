from django.shortcuts import render, HttpResponse, redirect
from django.core.serializers import serialize
# added by me
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from Home.models import USER

import requests
import json
import os
import time
from datetime import datetime, timedelta
# utils python functions
from Home.utils.geojsonfun import GEOJSON

# email verification
import uuid
from django.conf import settings
from django.core.mail import send_mail
# template email
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

# image verification
from PIL import Image

# decorators
from django.contrib.auth.decorators import login_required

import io
# for using model
import numpy as np
from PIL import Image
import tensorflow
from tensorflow.keras.models import load_model
from keras_preprocessing.image import img_to_array, load_img
from keras.applications.vgg19 import preprocess_input
####################################################################


def send_mail_after_registration(email,auth_token):
    subject = "Your account needs to be verified"

    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    plaintext = get_template('verificationEmail.txt')
    htmly     = get_template('verificationMail.html')

    d = {
        'auth_token': auth_token
    }
    
    text_content = plaintext.render(d)
    html_content = htmly.render(d)
    msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def verify(request,auth_token):
    try:
        user_obj = USER.objects.filter(auth_token=auth_token).first()
        if user_obj:
            if user_obj.is_verified == True:
                messages.success(request, "Your account already verified")
                return redirect("signin")
            else:
                user_obj.is_verified = True
                user_obj.save()
                messages.success(request, "Your account has been verified. Please Login")
                return redirect("signin")
        else:
            return render(request,"error.html",{"error":"Invalid token"})
    except Exception as e:
        print(e)
        return(redirect("tokensend"))

def signin(request):
    if request.method == "POST":
        userName = request.POST.get("userName")
        password = request.POST.get("password")

        user = authenticate(request, username = userName, password = password)

        if user is not None:
            queryObj = USER.objects.filter(username=userName)
            jsonObj = serialize("json", queryObj)
            arrOfDictObj = json.loads(jsonObj)
            USERobj = arrOfDictObj[0]["fields"]
            if USERobj['is_verified'] ==True:
                login(request, user)
                return redirect("home")
            else:
                messages.warning(request, "Your email is not verified. Please check you email")
                return redirect("signin")
        else:
            messages.warning(request, "Wrong credentials !")
            return redirect("signin")
    return render(request,"LoginRegister.html")

def register(request):
    if request.method == "POST":
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        userName = request.POST.get("userName")
        email = request.POST.get("email")
        password = request.POST.get("password")
        print(fname,lname,userName,email,password)
        if User.objects.filter(username=userName).exists() == True:
            messages.error(request, "Username already exists. Please try with another one")
            return render(request,"LoginRegister.html")
        elif User.objects.filter(email=email).exists() == True:
            messages.warning(request, "Email already exists. Please try with another one ")
            return render(request,"LoginRegister.html")
        else:
            # newUser = get_user_model().objects.create(userName,email,password)
            newUser = User.objects.create_user(userName, email, password)
            newUser.first_name = fname
            newUser.last_name = lname

            auth_token = str(uuid.uuid4())
            print(auth_token)
            newUSER = USER.objects.create(user=newUser,username=userName,auth_token=auth_token,fields="[]")

            newUser.save()
            newUSER.save()
            #############
            send_mail_after_registration(email, auth_token)
            return redirect("tokensend")
            # return redirect("signin")
    else:
        return render(request,"LoginRegister.html")

def tokensend(request):
    return render(request,"tokensend.html")

def signout(request):
    # delete image fields
    my_dir = str(os.getcwd())+"/static/fieldImages/"
    for fname in os.listdir(my_dir):
        if fname.startswith(request.user.username):
            os.remove(os.path.join(my_dir, fname))
    
    # delete plant image
    my_dir = str(os.getcwd())+"/static/uploads/"
    for fname in os.listdir(my_dir):
        if fname.startswith(request.user.username):
            os.remove(os.path.join(my_dir, fname))
    
    # delete session data
    if 'redirectDict' in request.session:
        del request.session["redirectDict"]
    logout(request)
    return redirect("signin")



# @login_required(login_url="/")
def home(request):
    if request.user.is_authenticated:
        context = {
            "fullName":request.user.first_name+' '+request.user.last_name
        }
        return render(request,"index.html",context)
    else:
        return redirect("signin")

def services(request):
    if request.user.is_authenticated:
        context = {
            "fullName":request.user.first_name+' '+request.user.last_name
        }
        return render(request,"services.html",context)
    else:
        return redirect("signin")

def contact(request):
    if request.user.is_authenticated:
        context = {
            "fullName":request.user.first_name+' '+request.user.last_name
        }
        return render(request,"contact.html",context)
    else:
        return redirect("signin")

def fields(request):
    if request.user.is_authenticated:
        # queryObj = USER.objects.filter(username = request.user.username)
        queryObj = USER.objects.filter(user=request.user)
        jsonObj = serialize("json", queryObj)
        arrOfDictObj = json.loads(jsonObj)
        USERobj = arrOfDictObj[0]
        dictionary = USERobj["fields"]
        data = dictionary["fields"]
        fields = []

        if data == "[]":
            context = {
            "fields": fields,
            "fullName":request.user.first_name+' '+request.user.last_name
            }
            return render(request,"fields.html",context)
        
        FieldList = json.loads(data)
        for field in FieldList:
            fielddict = {
                "username": field["username"],
                "fieldId": field["fieldId"],
                "cropType": field["cropType"],
                "area":field["area"],
                "sowingDate": field["sowingDate"],
                "fieldDiscription": field["fieldDiscription"]
            }
            fields.append(fielddict)

        context = {
            "fields": fields,
            "fullName":request.user.first_name+' '+request.user.last_name
        }
        return render(request,"fields.html",context)
    else:
        return redirect("signin")


def fieldAnalysis(request,v1,v2,username,fieldId):
    if request.user.is_authenticated and request.user.username ==username:
        if  v1 != "none":
            Begindatestring = v1[2:]
            Begindate = datetime.strptime(Begindatestring, "%y-%m-%d")
            date_start = "20" + (Begindate - timedelta(days=10,hours=0)).strftime("%y-%m-%d")
            date_end = "20" + Begindate.strftime("%y-%m-%d")
        else:
            date_start = "20" + (datetime.now() - timedelta(days=10,hours=0)).strftime("%y-%m-%d")
            date_end = "20" + (datetime.now() - timedelta(days=1,hours=0)).strftime("%y-%m-%d")
        
        if v2 != "none":
            index = v2
        else:
            index = "NDVI"

        # setting image name
        imageFileName = fieldId+index+date_end

        # checking user data in database 
        queryObj = USER.objects.filter(user=request.user)
        jsonObj = serialize("json", queryObj)
        arrOfDictObj = json.loads(jsonObj)
        USERobj = arrOfDictObj[0]
        dictionary = USERobj["fields"]
        data = dictionary["fields"]

        if data == "[]":
            return render(request,"error.html",{"error":"You don't have any field added .. please add a field first"})
        # data recieved in data
        fieldList = json.loads(data)
        targetField = {}
        for field in fieldList:
            if field["fieldId"]==fieldId:
                targetField = field
        coordinates = json.dumps(targetField["coord"])
        geojson = GEOJSON(targetField["cropType"],targetField["sowingDate"] ,targetField["year"] ,coordinates)
        # geojson created

        url1 = "https://api-connect.eos.com/field-management"
        payload1 = geojson
        headers = {
            "x-api-key" : settings.API_KEY
        }
        response1 = requests.request("POST", url1, headers=headers, data=payload1)
        print(response1.text)
        if response1.status_code != 201:
            return render(request,"error.html",{"error":"Status code:"+str(response1.status_code)+" Response:"+response1.text})
        dict1 = json.loads(response1.text)
        fieldIdNo = dict1["id"]

        ########################### weather data #########################
        urlW = "https://api-connect.eos.com/weather/forecast/"+str(fieldIdNo)
        v1 = '{"params":{"date_start":"'
        v2 = '","date_end":"'
        v3 = '"},"provider":"icon"}'
        dateWS = "20"+str((datetime.now()+timedelta(days=2)).strftime("%y-%m-%d"))
        dateWE = "20"+str((datetime.now()+timedelta(days=3)).strftime("%y-%m-%d"))
        payloadW = v1 + dateWS + v2 + dateWE + v3

        responseW = requests.request("POST", urlW, headers=headers, data=payloadW)
        if responseW.status_code != 200:
            return render(request,"error.html",{"error":"Status code:"+str(responseW.status_code)+" Response:"+responseW.text})

        listW = json.loads(responseW.text)
        tomorrowW = listW[0]
        dayAfterTomorrowW = listW[1]

        wind1 = str(tomorrowW["forecast"][4].get("wind"))[0:4]
        humidity1 = tomorrowW["forecast"][4].get("humidity")
        temp1 = tomorrowW["forecast"][4].get("temperature_max")
        cloud1 = tomorrowW["forecast"][4].get("cloudiness")
        weatherDate1 = tomorrowW["date"]
        wind2 = str(dayAfterTomorrowW["forecast"][4].get("wind"))[0:4]
        humidity2 = dayAfterTomorrowW["forecast"][4].get("humidity")
        temp2 = dayAfterTomorrowW["forecast"][4].get("temperature_max")
        cloud2 = dayAfterTomorrowW["forecast"][4].get("cloudiness")
        weatherDate2 = dayAfterTomorrowW["date"]

        #####################################################################

        # check if image exist already 
        my_dir = str(os.getcwd())+"/static/fieldImages/"
        for fname in os.listdir(my_dir):
            if fname ==imageFileName+".png":
                print('Image already exist imagename = '+imageFileName+" index="+index)
                context = {
                    "fullName":request.user.first_name+' '+request.user.last_name,
                    "imageFileName":imageFileName,
                    "username": request.user.username,
                    "fieldId": fieldId,
                    "index":index,
                    "viewdate":imageFileName[-10:],
                    "cloud1":cloud1,
                    "cloud2":cloud2,
                    "temp1":temp1,
                    "temp2":temp2,
                    "wind1":wind1,
                    "wind2":wind2,
                    "weatherDate1":weatherDate1,
                    "weatherDate2":weatherDate2
                }
                request.session["redirectDict"] = context
                return render(request,"fieldAnalysis.html",context)
        
        
        url2 = "https://api-connect.eos.com/scene-search/for-field/"+str(fieldIdNo)
        v1 = '{"params":{"date_start":"'
        v2 = '","date_end":"'
        v3 = '","data_source":["sentinel2"]}}'
        payload2 = v1 + date_start + v2 + date_end + v3

        response2 = requests.request("POST", url2, headers=headers, data=payload2)
        print(response2.text)
        if response2.status_code != 201:
            return render(request,"error.html",{"error":"Status code:"+str(response2.status_code)+" Response:"+response2.text})

        dict2 = json.loads(response2.text)
        reqId = dict2["request_id"]
        response2.close()


        url3 = "https://api-connect.eos.com/scene-search/for-field/"+str(fieldIdNo)+"/"+str(reqId)
        payload3 = ""
        time.sleep(12)#*******************************

        response3 = requests.request("GET", url3, headers=headers, data=payload3)
        if response3.status_code != 200:
            return render(request,"error.html",{"error":"Status code:"+str(response3.status_code)+" Response:"+response3.text})
        print(response3.text)
        dict3 = json.loads(response3.text)
        resultListOfDict = dict3["result"]
        i = len(resultListOfDict)-1
        viewId = resultListOfDict[i]["view_id"]
        viewdate = resultListOfDict[i]["date"]
        cloud = resultListOfDict[i]["cloud"]
        if v1 != "none":
            viewId = resultListOfDict[i]["view_id"]
            viewdate = resultListOfDict[i]["date"]
            cloud = resultListOfDict[i]["cloud"]
        else:
            while i!=-1:
                if resultListOfDict[i]["cloud"]==0.0:
                    viewId = resultListOfDict[i]["view_id"]
                    viewdate = resultListOfDict[i]["date"]
                    cloud = resultListOfDict[i]["cloud"]
                    break
            i = i-1
        request.session["redirectDict"] = {
            "fieldId": fieldId,
            "fieldIdNo": fieldIdNo,
            "index":index,
            "imageFileName":imageFileName,
            "viewId": viewId,
            "viewdate":viewdate,

            "cloud1":cloud1,
            "cloud2":cloud2,
            "temp1":temp1,
            "temp2":temp2,
            "wind1":wind1,
            "wind2":wind2,
            "weatherDate1":weatherDate1,
            "weatherDate2":weatherDate2
        }
        print("****** Now redirect to route1  *******")
        return redirect("route1")
    else:
        return redirect("signin")



def route1(request):
    if request.method == "POST":
        index = request.POST["index"]
        if index == "":
            index = "none"
        viewDate = request.POST["viewDate"]
        if viewDate == "":
            viewDate = "none"
        try:
            redirectDict = request.session["redirectDict"]
            fieldId = redirectDict["fieldId"]
        except Exception:
            return render(request,"error.html",{"error":"Please allow to store cookies"})
        
        print("******** Redirect to fieldAnalysis **********")
        return redirect("/fieldAnalysis/"+ viewDate+ "/"+ index +"/"+request.user.username+"/"+fieldId)
    else:
        print("***** Inside Route1 ******")
        if 'redirectDict' in request.session:
            do = True
        else:
            do = False
        if do == False:
            return render(request,"error.html",{"error":"Not allowed url"})
        
        redirectDict = request.session["redirectDict"]
        fieldId = redirectDict["fieldId"]
        fieldIdNo = redirectDict["fieldIdNo"]
        index = redirectDict["index"]
        imageFileName = redirectDict["imageFileName"]
        viewId = redirectDict["viewId"]
        viewdate = redirectDict["viewdate"]

        cloud1 = redirectDict["cloud1"]
        cloud2 = redirectDict["cloud2"]
        temp1 = redirectDict["temp1"]
        temp2 = redirectDict["temp2"]
        wind1 = redirectDict["wind1"]
        wind2 = redirectDict["wind2"]
        weatherDate1 = redirectDict["weatherDate1"]
        weatherDate2 = redirectDict["weatherDate2"]

        context = {
            "fullName":request.user.first_name+' '+request.user.last_name,
            "imageFileName":imageFileName,
            "index":index,
            "username": request.user.username,
            "fieldId": fieldId,
            "fieldIdNo":fieldIdNo,
            "viewId":viewId,
            "viewdate":viewdate,
            "cloud1":cloud1,
            "cloud2":cloud2,
            "temp1":temp1,
            "temp2":temp2,
            "wind1":wind1,
            "wind2":wind2,
            "weatherDate1":weatherDate1,
            "weatherDate2":weatherDate2
        }
        request.session["redirectDict"] = context

        # check if image exist already
        my_dir = str(os.getcwd())+"/static/fieldImages/"
        for fname in os.listdir(my_dir):
            if fname ==imageFileName+".png":
                print('Image already exist imagename = '+imageFileName+" index="+index)
                return render(request,"fieldAnalysis.html",context)

        url4 = "https://api-connect.eos.com/field-imagery/indicies/"+str(fieldIdNo)
        print(url4)
        headers = {
            "x-api-key" : settings.API_KEY
        }
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
        print(viewId)
        # Setting index
        p4Dict["params"]["index"] = index
        payload4 = json.dumps(p4Dict)
        time.sleep(0)#*******************************
        response4 = requests.request("POST", url4, headers=headers, data=payload4)
        if response4.status_code != 202:
            return render(request,"error.html",{"error":"Status code:"+str(response4.status_code)+" Response:"+response4.text})
        print(response4.text)
        dict4 = json.loads(response4.text)
        requestId = dict4["request_id"]

        url5 = "https://api-connect.eos.com/field-imagery/"+str(fieldIdNo)+"/"+str(requestId)
        print(url5)
        payload5 = ""

        time.sleep(10)
        response5 = requests.request("GET", url5, headers=headers, data=payload5)
        if response5.status_code != 200:
            return render(request,"error.html",{"error":"Status code:"+str(response5.status_code)+" Response:"+response5.text})
        

        if response5.headers["Content-Type"] == "binary/octet-stream":
            print("*** Binary response *****")
            # Saving image
            open(str(os.getcwd())+"/static/fieldImages/"+imageFileName+".png", 'wb').write(response5.content)
            try:
                img = Image.open(str(os.getcwd())+"/static/fieldImages/"+imageFileName+".png")
                img.verify()
                valid = True
            except Exception:
                valid = False
            
            if valid:
                return render(request,"fieldAnalysis.html",context)
            else:
                print("invalid image")
                os.remove(str(os.getcwd())+"/static/fieldImages/"+imageFileName+".png")
                return render(request,"fieldAnalysis.html",context)
        else:
            print("***** Not binary data ******")
            print(response5.text)
            return render(request,"fieldAnalysis.html",context)



def diseasePredict(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            imgName = request.user.username+"PLANT_IMAGE.jpg"

            # saving image from form data
            bytesio_object = request.FILES['plantImg'].file
            open(str(os.getcwd())+"/static/uploads/"+imgName, 'wb').write(bytesio_object.read())

            # my model
            MODEL_PATH = str(os.getcwd())+'/Home/Model/MyModel.h5'
            model = load_model(MODEL_PATH)

            CLASS_NAMES = ['Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust',
            'Apple___healthy', 'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew',
            'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
            'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Grape___Black_rot',
            'Grape___Esca_(Black_Measles)','Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
            'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
            'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight',
            'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy',
            'Soybean___healthy', 'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch',
            'Strawberry___healthy','Tomato___Bacterial_spot', 'Tomato___Early_blight',
            'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot',
            'Tomato___Spider_mites Two-spotted_spider_mite','Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
            'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
            ]

            path = str(os.getcwd())+"/static/uploads/"+imgName
            try:
                img = load_img(path, target_size = (256,256))
                imgArr = img_to_array(img)
                processedImg = preprocess_input(imgArr)
                finalImg = np.expand_dims(processedImg, axis=0)
                pred = model.predict(finalImg)
                diseaseClass = np.argmax(pred)
                print(diseaseClass)

                predicted_class = CLASS_NAMES[np.argmax(pred[0])]
                confidence = np.max(pred[0])
                context = {
                    "fullName":request.user.first_name+' '+request.user.last_name,
                    'Class': predicted_class,
                    'Confidence': str(confidence)
                }
                print(context)
                return render(request,"result.html",context)
            except Exception:
                return render(request,"error.html",{"error":"Invalid Imgage"})
        else:
            return render(request,"diseasePredict.html",{"fullName":request.user.first_name+' '+request.user.last_name})
    else:
        return redirect("signin")

def addNewField(request): 
    if request.method == "POST" and request.user.is_authenticated == True:

        coordinates = request.POST.get("coordinates")
        if(coordinates == "" or None):
            return redirect("addNewField")
        ################## code for adding new field data to database #######

        queryObj = USER.objects.filter(user=request.user)
        jsonObj = serialize("json", queryObj)
        arrOfDictObj = json.loads(jsonObj)
        USERobj = arrOfDictObj[0]
        dictionary = USERobj["fields"]
        data = dictionary["fields"]
        print(coordinates)

        geojson = GEOJSON(request.POST["cropType"],request.POST["sowingDate"] ,request.POST.get("sowingDate")[0:4] ,coordinates)
        # geojson created

        url1 = "https://api-connect.eos.com/field-management"
        payload1 = geojson
        headers = {
            "x-api-key" : settings.API_KEY
        }
        response1 = requests.request("POST", url1, headers=headers, data=payload1)
        # print(response1.text)
        if response1.status_code != 201:
            return render(request,"error.html",{"error":"Status code:"+str(response1.status_code)+" Response:"+response1.text})
        dict1 = json.loads(response1.text)
        area = dict1["area"]

        fieldDiscription = request.POST.get("fieldName")
        cropType = request.POST.get("cropType")
        sowingDate = request.POST.get("sowingDate")
        year = sowingDate[0:4]

        listField = json.loads(data)

        newFieldGeojsonStr = GEOJSON(cropType, sowingDate, year, coordinates)
        fielddict = {
            "username" : request.user.username,
            "fieldId": request.user.username+str(len(listField)+1),
            "cropType" : cropType,
            "sowingDate" : sowingDate,
            "year" : year,
            "area": area,
            "fieldDiscription" : fieldDiscription,
            "coord": json.loads(coordinates)
        }


        listField.append(fielddict)
        finaldata = json.dumps(listField)
        userobj = USER.objects.get(user = request.user)
        userobj.fields = finaldata
        userobj.save()
        return redirect("/fieldAnalysis/none/none/"+fielddict["username"]+"/"+fielddict["fieldId"])


    if request.user.is_authenticated:
        context = {
            "fullName":request.user.first_name+' '+request.user.last_name
        }
        return render(request,"addNewField.html",context)
    else:
        return redirect("signin")

def weather(request):
    return render(request,"weatherForcast.html")






























    