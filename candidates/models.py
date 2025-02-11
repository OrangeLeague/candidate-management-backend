from django.db import models
import uuid

class Team(models.Model):
    USER_ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('candidate', 'Candidate'),
    ]
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # Store hashed passwords in a real-world scenario
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=USER_ROLE_CHOICES,null=True, blank=True)  # New field to differentiate roles

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'candidates_team'

class Candidate(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Selected', 'Selected'),
        ('Rejected', 'Rejected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Use UUID for unique IDs
    name = models.CharField(max_length=200)
    years_of_experience = models.IntegerField()
    skillset = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    cv = models.FileField(upload_to='cvs/')
    email=models.CharField(max_length=200,null=True, blank=True)
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
    rejected_by = models.ManyToManyField(Team, related_name='rejected_candidates', blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)  # New field to store interview scheduled time
    notice_period=models.IntegerField(null=True, blank=True)
    current_company=models.CharField(max_length=200, blank=True)
    qualification=models.CharField(max_length=200, blank=True)
    current_location=models.CharField(max_length=200, blank=True)
    vendor=models.CharField(max_length=200,default='OLVT', blank=True)
    file_url = models.URLField(max_length=1024,null=True, blank=True)  # Store the public URL of the file
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'candidates_candidate'

class RejectionComment(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='rejection_comments')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.team.name} on {self.candidate.name}"

# New Model for Storing Candidate Time Slots
class TimeSlot(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    time = models.TimeField()
    created_by = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_time_slots')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Slot for {self.candidate.name} on {self.date} at {self.time}"

    class Meta:
        db_table = 'candidates_timeslot'
        unique_together = ['candidate', 'date', 'time']  # Ensures no duplicate time slots for the same candidate

#Models for hr and interviewer application
class HrTeam(models.Model):
    USER_ROLE_CHOICES = [
        ('hr', 'Hr'),
        ('interviewer', 'Interviewer'),
    ]
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # Store hashed passwords in a real-world scenario
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=11, choices=USER_ROLE_CHOICES,null=True, blank=True)  # New field to differentiate roles

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'hr_team'

class Interviewer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Use UUID for unique IDs
    name = models.CharField(max_length=200)
    years_of_experience = models.IntegerField()
    skillset = models.CharField(max_length=200)
    email=models.CharField(max_length=200,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'interviewer_details'

# New Model for Storing Candidate Time Slots
class InterviewerTimeSlot(models.Model):
    interviewer = models.ForeignKey(Interviewer, on_delete=models.CASCADE, related_name='interviewer_time_slots')
    date = models.DateField()
    time = models.TimeField()
    created_by = models.ForeignKey(HrTeam, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_time_slots')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Slot for {self.interviewer.name} on {self.date} at {self.time}"

    class Meta:
        db_table = 'interviewer_timeslot'
        unique_together = ['interviewer', 'date', 'time']  # Ensures no duplicate time slots for the same candidate