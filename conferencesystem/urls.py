from django.urls import path
from . import views

from project import settings

from django.conf.urls.static import static

app_name = "conferencesystem"
urlpatterns = [
    path('', views.index, name='index'),
    path('conferences/', views.conferences, name='conferences'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    
    path('view_papers/', views.view_user_papers, name='view_user_papers'),
    path('papers/<int:paper_id>', views.paper_detail, name='paper_detail'),
    path('papers/<int:paper_id>/download_paper', views.download_paper, name='download_paper'),
    path('papers/<int:paper_id>/review_paper', views.review_paper, name='review_paper'),
    path('papers/<int:paper_id>/add_reviewers/', views.add_reviewers, name='add_reviewers'),
    path('papers/<int:paper_id>/remove_reviewer/<int:reviewer_id>', views.remove_reviewer, name='remove_reviewer'),

    path('conference/<int:conference_id>/', views.conference_details, name='conference_details'),
    path('conference/<int:conference_id>/submit_paper/', views.submit_paper, name='submit_paper'),
    path('conference/<int:conference_id>/view_papers/', views.view_conference_papers, name='view_conf_papers'),
]