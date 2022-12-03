from django.contrib import admin
from django.urls import path,include
from Home import views

urlpatterns = [
    path("login/", views.signin, name="signin"),
    path("register/", views.register, name="register"),
    path("tokensend/",views.tokensend,name="tokensend"),
    path("verify/<auth_token>",views.verify,name="verify"),
    path("logout/", views.signout, name="logout"),
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact, name="contact"),
    path("fields/",views.fields, name="fields"),
    path("addNewField/", views.addNewField, name="addNewField"),
    path("fieldAnalysis/<v1>/<v2>/<username>/<fieldId>", views.fieldAnalysis, name="fieldAnalysis"),
    path("route1", views.route1, name="route1"),
    path("diseasePredict", views.diseasePredict, name="diseasePredict"),
    path("weather/", views.weather, name="weather"),
]
