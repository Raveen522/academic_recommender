from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("interest-selection/", views.interest_selection_view, name="interest_selection"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    # path("react-to-article/", views.react_to_article, name="react_to_article"),
    path('react/', views.react_to_article, name='react_to_article'),
    # path("rate_article/", views.rate_article, name="rate_article"),
    # path('rate-article/', views.rate_article, name='rate_article'),
]
