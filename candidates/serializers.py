from rest_framework import serializers
from .models import Team, Candidate,RejectionComment,HrTeam,Interviewer

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'username', 'password', 'name','role']

class RejectionCommentSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)  # Nested serializer for team details
    class Meta:
        model = RejectionComment
        fields = ['id', 'team', 'comment', 'created_at']

class CandidateSerializer(serializers.ModelSerializer):
    rejection_comments = RejectionCommentSerializer(many=True, read_only=True)
    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'years_of_experience', 
            'skillset', 'status', 'cv', 'team', 'rejected_by','rejection_comments','notice_period','current_company','qualification','current_location','vendor','file_url','email'
        ]

#serializers for hr and interviewer application
class HrSerializer(serializers.ModelSerializer):
    class Meta:
        model = HrTeam
        fields = ['id', 'username', 'password', 'name','role']

class InterviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interviewer
        fields = [
            'id', 'name', 'years_of_experience', 
            'skillset','email'
        ]