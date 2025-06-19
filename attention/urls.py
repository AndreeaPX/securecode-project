from django.urls import path
from .views import attention_check, attention_end, attention_feedback

urlpatterns = [
    path("check/", attention_check),
    path("end/", attention_end), 
    path("feedback/", attention_feedback),
]
