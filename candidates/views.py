from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Team, Candidate
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q
from rest_framework.views import APIView
from .serializers import TeamSerializer, CandidateSerializer
from rest_framework import status
from .models import Team, Candidate
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from json import loads
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

# Manual Login View
@csrf_exempt
def login_view(request):
    print(request,'request1')
    if request.method == 'POST':
        import json
        data = json.loads(request.body)  # Parse JSON body from React
        username = data.get('username')
        password = data.get('password')

        try:
            team = Team.objects.get(username=username, password=password)
            # Create a mock token for now (use JWT in production)
            print(team.id,'teamsdfsdfsdf')
            request.session['team_id'] = team.id
            request.session.save()
            print(f"Session data: {request.session.items()}")
            token = f"mock-token-{team.id}"
            print(request,'request12')
            return JsonResponse({
                "access": token,
                "message": "Login successful"
            }, status=200)
        except Team.DoesNotExist:
            return JsonResponse({"detail": "Invalid credentials"}, status=400)

    return JsonResponse({"detail": "Invalid request method"}, status=405)

# Logout View
@csrf_exempt
def logout_view(request):
    if 'team_id' in  request.session:
        del request.session['team_id']
        print(f"Session data3: {request.session.items()}")
        return JsonResponse({"message": "Successfully logged out"}, status=200)
    return JsonResponse({"error": "No active session found"}, status=400)

def candidate_list(request):
    """
    View to fetch candidates visible to the logged-in team.
    """
    team_id = request.session.get('team_id')
    if not team_id:
        return JsonResponse({"error": "Unauthorized access"}, status=401)

    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return JsonResponse({"error": "Team not found"}, status=404)

    # Fetch candidates visible to the team
    candidates = Candidate.objects.filter(
        Q(team__isnull=True, status="Open") |  # Open candidates visible to all teams
        Q(team=team)  # Candidates assigned to this team
    ).exclude(  # Exclude candidates rejected by the current team
        Q(rejected_by=team)
    )

    candidates_data = [
        {
            "id": candidate.id,
            "name": candidate.name,
            "years_of_experience": candidate.years_of_experience,
            "skillset": candidate.skillset,
            "status": candidate.status,
            "cv": candidate.cv.url if candidate.cv else None,
            "team": candidate.team.name if candidate.team else None,
        }
        for candidate in candidates
    ]

    return JsonResponse({"candidates": candidates_data})

@csrf_exempt
def update_status(request, candidate_id, status):
    """
    View to update candidate status by the logged-in team.
    """
    team_id = request.session.get('team_id')
    if not team_id:
        return JsonResponse({"error": "Unauthorized access"}, status=401)

    try:
        team = Team.objects.get(id=team_id)
        candidate = Candidate.objects.get(id=candidate_id)
    except Team.DoesNotExist:
        return JsonResponse({"error": "Team not found"}, status=404)
    except Candidate.DoesNotExist:
        return JsonResponse({"error": "Candidate not found"}, status=404)

    # Logic to update candidate status
    if status == 'Interview Scheduled' and candidate.status == 'Open':
        candidate.status = 'Interview Scheduled'
        candidate.team = team
        candidate.rejected_by.clear()  # Clear rejection history if the status changes
    elif status == 'Selected' and candidate.team == team:
        candidate.status = 'Selected'
        candidate.rejected_by.clear()  # Clear rejection history if the candidate is selected
    elif status == 'Rejected' and candidate.team == team:
        candidate.status = 'Open'
        candidate.team = None  # Make candidate visible to all other teams
        candidate.rejected_by.add(team)  # Add the rejecting team to the rejection history
    elif status == 'Open' and candidate.status == 'Rejected' and candidate.team == team:
        candidate.status = 'Open'
        candidate.team = None  # Make candidate visible to all teams again
        candidate.rejected_by.clear()  # Clear rejection history

    candidate.save()

    return JsonResponse({
        "message": f"Candidate status updated to {candidate.status}",
        "candidate": {
            "id": candidate.id,
            "name": candidate.name,
            "status": candidate.status,
            "team": candidate.team.name if candidate.team else None,
        }
    }, status=200)

@csrf_exempt
def add_team(request):
    if request.method == "POST":
        try:
            # Parse JSON data from the request
            data = loads(request.body)
        except ValueError:
            return JsonResponse({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        # Use the serializer to validate and save the data
        serializer = TeamSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({"error": "Only POST method is allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@csrf_exempt
def get_teams(request):
    """
    Retrieve all teams.
    """
    if request.method == "GET":
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True)
        return JsonResponse(serializer.data, safe=False)
    return JsonResponse({"error": "Only GET method is allowed"}, status=405)

@csrf_exempt
def delete_team(request, pk):
    """
    Delete a team by its primary key (pk).
    """
    if request.method == "DELETE":
        try:
            team = Team.objects.get(pk=pk)
            team.delete()
            return JsonResponse({"message": "Team deleted successfully."}, status=200)
        except Team.DoesNotExist:
            return JsonResponse({"error": "Team not found."}, status=404)
    return JsonResponse({"error": "Only DELETE method is allowed"}, status=405)

@api_view(['GET'])
def get_candidates(request):
    """
    Retrieve all candidates.
    """
    candidates = Candidate.objects.all()
    serializer = CandidateSerializer(candidates, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def add_candidate(request):
    """
    Add a new candidate.
    """
    serializer = CandidateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_candidate(request, pk):
    """
    Delete a specific candidate by ID.
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.delete()
    return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)


# # View for CRUD operations on teams
# @method_decorator(csrf_exempt, name='dispatch')
# class TeamAdminView(APIView):
#     def get(self, request):
#         teams = Team.objects.all()
#         serializer = TeamSerializer(teams, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = TeamSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
#         return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         try:
#             team = Team.objects.get(pk=pk)
#             team.delete()
#             return Response({"message": "Team deleted successfully."}, status=status.HTTP_200_OK)
#         except Team.DoesNotExist:
#             return Response({"error": "Team not found."}, status=status.HTTP_404_NOT_FOUND)

# # View for CRUD operations on candidates
# @method_decorator(csrf_exempt, name='dispatch')
# class CandidateAdminView(APIView):
#     def get(self, request):
#         candidates = Candidate.objects.all()
#         serializer = CandidateSerializer(candidates, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = CandidateSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, pk):
#         try:
#             candidate = Candidate.objects.get(pk=pk)
#             candidate.delete()
#             return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)
#         except Candidate.DoesNotExist:
#             return Response({"error": "Candidate not found."}, status=status.HTTP_404_NOT_FOUND)
