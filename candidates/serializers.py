from rest_framework import serializers
from .models import Team, Candidate

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'username', 'password', 'name']

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'years_of_experience', 
            'skillset', 'status', 'cv', 'team', 'rejected_by'
        ]