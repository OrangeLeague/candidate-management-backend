from django.contrib import admin
from .models import Team, Candidate

class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'name')  # Use 'username' instead of 'user'

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'years_of_experience', 'skillset', 'status', 'team')

admin.site.register(Team, TeamAdmin)
admin.site.register(Candidate, CandidateAdmin)
