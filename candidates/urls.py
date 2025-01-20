from django.urls import path
from . import views
# from .views import TeamAdminView, CandidateAdminView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.candidate_list, name='candidate_list'),
    path('update_status/<uuid:candidate_id>/<str:status>/', views.update_status, name='update_status'),

    # path('admin/teams/', TeamAdminView.as_view(), name='admin_teams'),
    # path('admin/candidates/', CandidateAdminView.as_view(), name='admin_candidates'),
    path('admin/teams/add', views.add_team, name='admin_teams'),
    path('admin/teams/get-teams', views.get_teams, name='admin_teams'),
    path('admin/teams/<uuid:pk>/', views.delete_team, name='delete_team'),

    path('admin/candidates/get-candidates', views.get_candidates, name='get_candidates'),  # Retrieve all candidates
    path('admin/candidates/add', views.add_candidate, name='add_candidate'),  # Add a new candidate
    path('admin/candidates/<uuid:pk>/', views.delete_candidate, name='delete_candidate'),  # Delete a candidate by ID
    path('admin/candidates/<uuid:pk>/update', views.update_candidate, name='update_candidate'),  # Update a candidate by ID

    path('time-slots/bulk-schedule/', views.bulk_schedule_time_slots, name='bulk_schedule_time_slots'),
    path('get-candidates/<uuid:candidate_id>/time-slots/', views.get_candidate_time_slots, name='get_candidate_time_slots'),
    path('get-candidate-name/<uuid:candidate_id>/', views.get_candidate_name, name='get_candidate_name'),
    path('request-time-slots/', views.request_time_slots, name='request_time_slots'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)