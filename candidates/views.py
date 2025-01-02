from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Team, Candidate
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.db.models import Q
from rest_framework.views import APIView
from .serializers import TeamSerializer, CandidateSerializer
from rest_framework import status
from .models import Team, Candidate, RejectionComment,TimeSlot
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from json import loads
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
import json
from datetime import datetime
from django.core.exceptions import ValidationError
from .utils.backblaze import BackblazeB2
# from candidates.utils.backblaze import BackblazeB2
import os

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
                "message": "Login successful",
                "team_id":team.id
            }, status=200)
        except Team.DoesNotExist:
            return JsonResponse({"detail": "Invalid credentials"}, status=400)

    return JsonResponse({"detail": "Invalid request method"}, status=405)

# Logout View
@csrf_exempt
def logout_view(request):
    print(f"Cookies: {request.COOKIES}")
    print(f"Session Key: {request.session.session_key}")
    print(f"Session Data Before: {request.session.items()}")
    if 'team_id' in  request.session:
        del request.session['team_id']
        print(f"Session data3: {request.session.items()}")
        return JsonResponse({"message": "Successfully logged out"}, status=200)
    return JsonResponse({"error": "No active session found"}, status=400)

@csrf_exempt
def candidate_list(request):
    """
    View to fetch candidates visible to the logged-in team.
    """
    print(f"Cookies: {request.COOKIES}")
    print(f"Session Items: {request.session.items()}")
    print(f"Session Key: {request.session.session_key}")
    # team_id = request.session.get('team_id')
    print(request.GET,'sdfsdfsdf')
    team_id = request.GET.get('activeTeamId')
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
            "scheduled_time":candidate.scheduled_time if candidate.scheduled_time else None,
            "current_company":candidate.current_company if candidate.current_company else None,
            "current_location":candidate.current_location if candidate.current_company else None,
            "qualification":candidate.qualification if candidate.qualification else None,
            "notice_period":candidate.notice_period if candidate.notice_period else None,
            "vendor":candidate.vendor if candidate.vendor else None,
            "file_url":candidate.file_url if candidate.file_url else None,
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

    data = json.loads(request.body)  # Parse JSON body
    comment = data.get('comment')
    # Logic to update candidate status
    if status == 'Interview Scheduled' and candidate.status == 'Open':
        candidate.status = 'Interview Scheduled'
        candidate.team = team
        candidate.rejected_by.clear()  # Clear rejection history if the status changes
        print(f"scheduled_time: {request}")
        scheduled_time = data.get('scheduled_time')
        if scheduled_time:
            candidate.scheduled_time = datetime.strptime(scheduled_time, "%Y-%m-%d %I:%M %p")
            # candidate.scheduled_time = scheduled_time
        else:
            return JsonResponse({"error": "Scheduled time is required"}, status=400)
    elif status == 'Selected' and candidate.team == team:
        candidate.status = 'Selected'
        candidate.rejected_by.clear()  # Clear rejection history if the candidate is selected
        candidate.scheduled_time=None
    elif status == 'Rejected' and candidate.team == team:
        candidate.status = 'Open'
        candidate.team = None  # Make candidate visible to all other teams
        candidate.scheduled_time=None
        candidate.rejected_by.add(team)  # Add the rejecting team to the rejection history
        if comment:
            RejectionComment.objects.create(candidate=candidate, team=team, comment=comment)
        else:
            return JsonResponse({"error": "Comment is required for rejection"}, status=400)
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
    print('started function')
    if request.FILES.get('cv'):
        print('started1 function')
        file = request.FILES['cv']
        print(file.name,'started2')
        file_name = file.name

        # Save the file temporarily
        temp_path = f"/tmp/{file_name}"
        with open(temp_path, 'wb+') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
        print('started3...')
        # Upload the file to Backblaze
        b2 = BackblazeB2()
        print('started3@@@')
        try:
            print('started3')
            # file_url = b2.upload_file(temp_path, file_name)
            file_url = b2.generate_presigned_url(file_name)
            print(f"File uploaded successfully: {file_url}")
            os.remove(temp_path)  # Remove the temporary file
            # Include the file URL in the request data
            request.data['file_url'] = file_url
        except Exception as e:
            print(f"File upload failed: {str(e)}")
            os.remove(temp_path)  # Ensure temp file is removed on error
            return Response({'error': f'File upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    serializer = CandidateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if not serializer.is_valid():
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_candidate(request, pk):
    """
    Delete a specific candidate by ID.
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.delete()
    return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)

def parse_time(time_str):
    """
    Convert time in 'HH:MM AM/PM' format to a Python time object.
    """
    try:
        # Parse the time string using datetime.strptime
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        return time_obj
    except ValueError:
        raise ValidationError(f"Invalid time format: {time_str}. Expected format is 'HH:MM AM/PM'.")

def get_time_slots_for_half(half):
    """
    Get predefined time slots based on the half (1st or 2nd).
    """
    if half == "1st half":
        return ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM"]
    elif half == "2nd half":
        return ["12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"]
    else:
        return []


@csrf_exempt
# @login_required
def bulk_schedule_time_slots(request):
    if request.method == "POST":
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)

            # Validate that the data is in the expected format (dictionary with dates as keys)
            if not isinstance(data, dict):
                return JsonResponse({"error": "Invalid data format. Expected a dictionary with dates as keys."}, status=400)

            # Extract candidate ID from the data
            candidate_id = data.get("candidate")
            if not candidate_id:
                return JsonResponse({"error": "Candidate ID is required."}, status=400)

            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                return JsonResponse({"error": f"Candidate with ID {candidate_id} does not exist."}, status=400)

            # List to hold created time slots for response
            created_slots = []

            for date, time_slots in data.items():
                # Skip "candidate" key if it is present
                if date == "candidate":
                    continue

                # Validate that time slots are a list
                if not isinstance(time_slots, list):
                    return JsonResponse({"error": f"Invalid time slots for {date}. Expected a list of time slots."}, status=400)

                # Loop through the time slots for this date
                for time_str in time_slots:
                    if time_str in ["1st half", "2nd half"]:
                        # If it's "1st half" or "2nd half", get the predefined time slots
                        predefined_slots = get_time_slots_for_half(time_str)
                        for slot in predefined_slots:
                            # Convert the slot to a valid time format
                            time_obj = parse_time(slot)

                            # Check if the time slot already exists for the candidate on this date and time
                            if TimeSlot.objects.filter(candidate=candidate, date=date, time=time_obj).exists():
                                continue  # Skip if this slot already exists

                            # Create the time slot
                            time_slot = TimeSlot.objects.create(
                                candidate=candidate,
                                date=date,
                                time=time_obj,
                                created_by=request.user if request.user.is_authenticated else None
                            )

                            # Add the created time slot to the list for response
                            created_slots.append({
                                "id": time_slot.id,
                                "candidate": candidate.id,
                                "date": time_slot.date,
                                "time": time_slot.time.strftime('%I:%M %p'),
                                "created_by": time_slot.created_by.id if time_slot.created_by else None,
                                "created_at": time_slot.created_at.isoformat(),
                            })
                    else:
                        # If it's a specific time (not 1st/2nd half), directly process it
                        time_obj = parse_time(time_str)

                        # Check if the time slot already exists for the candidate on this date and time
                        if TimeSlot.objects.filter(candidate=candidate, date=date, time=time_obj).exists():
                            continue  # Skip if this slot already exists

                        # Create the time slot
                        time_slot = TimeSlot.objects.create(
                            candidate=candidate,
                            date=date,
                            time=time_obj,
                            created_by=request.user if request.user.is_authenticated else None
                        )

                        # Add the created time slot to the list for response
                        created_slots.append({
                            "id": time_slot.id,
                            "candidate": candidate.id,
                            "date": time_slot.date,
                            "time": time_slot.time.strftime('%I:%M %p'),
                            "created_by": time_slot.created_by.id if time_slot.created_by else None,
                            "created_at": time_slot.created_at.isoformat(),
                        })

            return JsonResponse({"created_slots": created_slots}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Only POST method is allowed."}, status=405)

def get_candidate_time_slots(request, candidate_id):
    """
    Fetch all time slots for a given candidate by ID.
    """
    try:
        # Check if the candidate exists
        time_slots = TimeSlot.objects.filter(candidate_id=candidate_id).order_by('date', 'time')

        if not time_slots.exists():
            return JsonResponse({"message": f"No time slots found for candidate ID {candidate_id}."}, status=404)

        # Prepare the response data
        response_data = {}
        for slot in time_slots:
            date_key = slot.date.isoformat()  # Group by date in ISO format
            if date_key not in response_data:
                response_data[date_key] = []
            response_data[date_key].append(slot.time.strftime("%I:%M %p"))  # Format time in HH:MM AM/PM

        return JsonResponse({"candidate_id": candidate_id, "time_slots": response_data}, status=200)

    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
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

def upload_resume(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = file.name

        # Save the file temporarily
        temp_path = f"/tmp/{file_name}"
        with open(temp_path, 'wb+') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)

        # Upload the file to Backblaze
        b2 = BackblazeB2()
        try:
            file_url = b2.upload_file(temp_path, file_name)
            os.remove(temp_path)  # Remove the temporary file

            # Save file information in the database
            resume = Candidate.objects.create(name=file_name, file_url=file_url)
            return JsonResponse({'message': 'File uploaded successfully', 'file_url': file_url})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)