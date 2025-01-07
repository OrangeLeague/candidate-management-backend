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
from django.core.files.storage import default_storage
import os
import boto3
from botocore.exceptions import ClientError
import io
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie


AWS_ACCESS_KEY_ID = 'AKIAS2VS4NCUU2RN32G4'
AWS_SECRET_ACCESS_KEY = '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'
S3_BUCKET = 'olvttalentspherebucket'

@ensure_csrf_cookie
def csrf_view(request):
    return JsonResponse({"csrfToken": request.META.get("CSRF_COOKIE")})

def s3_client():
    """
    Create and return an S3 client using the provided credentials.
    """
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        return s3
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        raise e
def upload_to_s3(file_content, s3_object_key, content_type=None):
    """
    Uploads file to S3 bucket.

    :param file_content: File content to be uploaded (bytes)
    :param s3_object_key: S3 object key (path inside the bucket)
    :param content_type: MIME type of the file (e.g., 'application/pdf')
    :return: S3 URL of the uploaded file
    """
    try:
        s3 = s3_client()
        print('entered into s3 bucket')
        s3_bucket = S3_BUCKET
        print('s3_bucket',s3_bucket)

        # Upload file to S3 bucket
        s3.upload_fileobj(
            io.BytesIO(file_content),
            s3_bucket,
            s3_object_key,
            ExtraArgs={'ContentType': content_type or 'application/octet-stream'}
        )

        # Generate and return the file URL
        s3_url = f'https://{s3_bucket}.s3.amazonaws.com/{s3_object_key}'
        print(f"File successfully uploaded to: {s3_url}")
        return s3_url

    except ClientError as e:
        print(f"Failed to upload file to S3: {e}")
        raise e
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        raise e
# Manual Login View
@csrf_exempt
# @ensure_csrf_cookie
def login_view(request):
    print(request,'request1')
    if request.method == 'POST':
        import json
        data = json.loads(request.body)  # Parse JSON body from React
        username = data.get('username')
        password = data.get('password')
        print(username,'username')

    #     # Debug: Check if user exists
    #     print(f"User exists1: {user_exists}")
    #     user_exists = User.objects.filter(username=username).exists()
    #     print(f"User exists: {user_exists}")
        
    #     print('above')
    #     user = authenticate(request, username=username, password=password)
    #     print('below')
    #     print(user,'usererr')
    #     if user is not None:
    #         login(request, user)  # Set session
    #         return JsonResponse({
    #             "message": "Login successful",
    #             "team_id": user.id,
    #             "username": user.username
    #         }, status=200)
    #     else:
    #         return JsonResponse({"detail": "Invalid credentials"}, status=400)

    # return JsonResponse({"detail": "Invalid request method"}, status=405)

        try:
            team = Team.objects.get(username=username, password=password)
            # Create a mock token for now (use JWT in production)
            print(f"Cookies12: {request.COOKIES}")
            print(f"Session Key12: {request.session.session_key}")
            print(team.id,'teamsdfsdfsdf')
            request.session['team_id'] = team.id
            # request.session.save()
            print(f"Session data12: {request.session.items()}")
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
    # Authenticate user

# Logout View
@csrf_exempt
# @ensure_csrf_cookie
def logout_view(request):
    print(f"Cookies: {request.COOKIES}")
    print(f"Session Key: {request.session.session_key}")
    print(f"Session Data Beforesss: {request.session.items()}")
    # if 'team_id' in  request.session:
    #     del request.session['team_id']
    #     print(f"Session data3: {request.session.items()}")
    #     return JsonResponse({"message": "Successfully logged out"}, status=200)
    # return JsonResponse({"error": "No active session found"}, status=400)

    if request.method == 'POST':
        logout(request)  # Clear session
        return JsonResponse({"message": "Successfully logged out"}, status=200)
    return JsonResponse({"detail": "Invalid request method"}, status=405)

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
    print('entered')
    """
    View to update candidate status by the logged-in team.
    """
    print('ssdsdfsdfs......dfsdfsdfsdfsdf')
    data = json.loads(request.body)  # Parse JSON body
    # team_id = request.session.get('team_id')
    team_id=data.get('activeTeamId')
    print(f"Session Itemssasas: {request.session.items()}")
    if not team_id:
        return JsonResponse({"error": "Unauthorized access"}, status=401)

    try:
        team = Team.objects.get(id=team_id)
        candidate = Candidate.objects.get(id=candidate_id)
    except Team.DoesNotExist:
        return JsonResponse({"error": "Team not found"}, status=404)
    except Candidate.DoesNotExist:
        return JsonResponse({"error": "Candidate not found"}, status=404)

    # data = json.loads(request.body)  # Parse JSON body
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
    # print('started function')
    # if request.FILES.get('cv'):
    #     print('started1 function')
    #     file = request.FILES['cv']
    #     print(file.name,'started2')
    #     file_name = file.name

    #     # Save the file temporarily
    #     temp_path = f"/tmp/{file_name}"
    #     with open(temp_path, 'wb+') as temp_file:
    #         for chunk in file.chunks():
    #             temp_file.write(chunk)
    #     print('started3...')
    #     # Upload the file to Backblaze
    #     b2 = BackblazeB2()
    #     print('started3@@@')
    #     try:
    #         print('started3')
    #         file_url = b2.upload_file(temp_path, file_name)
    #         # file_url = b2.generate_presigned_url(file_name)
    #         print(f"File uploaded successfully: {file_url}")
    #         os.remove(temp_path)  # Remove the temporary file
    #         # Include the file URL in the request data
    #         request.data['file_url'] = file_url
    #     except Exception as e:
    #         print(f"File upload failed: {str(e)}")
    #         os.remove(temp_path)  # Ensure temp file is removed on error
    #         return Response({'error': f'File upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # if request.FILES.get('cv'):
    #     file = request.FILES['cv']
    #     print(f"File: {file.name}")

    #     # Create a new Candidate instance with the uploaded file
    #     candidate = Candidate(cv=file)
    #     candidate.save()

    # serializer = CandidateSerializer(data=request.data)
    # if serializer.is_valid():
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    # if not serializer.is_valid():
    #     print(serializer.errors)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



    # if request.FILES.get('cv'):
    #     file = request.FILES['cv']
    #     print(f"File: {file.name}")

    #     # Save file using Django's default storage
    #     file_path = default_storage.save(f'media/cvs/{file.name}', file)
    #     print(f"File saved to: {file_path}")

    #     # Temporarily add the file to the request data for serializer validation
    #     mutable_data = request.data.copy()
    #     mutable_data['cv'] = file_path

    #     # Use serializer to validate and save the data
    #     serializer = CandidateSerializer(data=mutable_data)
    #     print('entered1')
    #     if serializer.is_valid():
    #         print('entered2')
    #         serializer.save()
    #         print(f"File saved to")
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     else:
    #         print(serializer.errors)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # else:
    #     # If no 'cv' file is provided
    #     return Response({'error': 'No CV file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

    if request.FILES.get('cv'):
        try:
            # Get the file from the request
            file = request.FILES['cv']
            print('entereddsd')
            file_content = file.read()
            # print('dfd',file_content)
            if not file_content:
                raise ValueError("File content is empty")
            file_name = file.name
            print('file_name',file_name)
            # Generate a unique S3 object key
            s3_object_key = f"cvs/{file_name}"

            # Upload the file to S3
            print('above')
            s3_url = upload_to_s3(file_content, s3_object_key, content_type=file.content_type)
            print(f"File uploaded to S3: {s3_url}")

            # Update the request data to include the S3 URL
            mutable_data = request.data.copy()
            mutable_data['file_url'] = s3_url

            # Validate and save the data using the serializer
            serializer = CandidateSerializer(data=mutable_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ClientError as e:
            print(f"S3 Upload failed: {e}")
            return Response({'error': 'Failed to upload CV to S3'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        # If no 'cv' file is provided
        return Response({'error': 'No CV file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_candidate(request, pk):
    """
    Delete a specific candidate by ID.
    """
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.delete()
    return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)

@api_view(['PUT'])
def update_candidate(request, pk):
    """
    Update a specific candidate by ID.
    """
    candidate = get_object_or_404(Candidate, pk=pk)

    # Check if the request contains a CV file
    if request.FILES.get('cv'):
        try:
            # Get the file from the request
            file = request.FILES['cv']
            file_content = file.read()
            if not file_content:
                raise ValueError("File content is empty")
            file_name = file.name

            # Generate a unique S3 object key
            s3_object_key = f"cvs/{file_name}"

            # Upload the file to S3
            s3_url = upload_to_s3(file_content, s3_object_key, content_type=file.content_type)

            # Update the request data to include the S3 URL
            mutable_data = request.data.copy()
            mutable_data['file_url'] = s3_url
        except ClientError as e:
            return Response({'error': 'Failed to upload CV to S3'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    print(candidate.status,'testing',request.data)
    # Preserve the current status if it's not provided in the request
    if 'status' not in request.data:
        request.data['status'] = candidate.status

    # Validate and update the candidate using the serializer
    serializer = CandidateSerializer(candidate, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

def get_candidate_name(request, candidate_id):
    """
    Retrieve the candidate's name based on the candidate ID.

    Args:
        request: The HTTP request object.
        candidate_id: The ID of the candidate.

    Returns:
        JsonResponse: The candidate's name or an error message if not found.
    """
    try:
        candidate = get_object_or_404(Candidate, id=candidate_id)
        return JsonResponse({"candidate_name": candidate.name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)