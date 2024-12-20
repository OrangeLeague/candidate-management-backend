from django.db import models

class Team(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # Store hashed passwords in a real-world scenario
    name = models.CharField(max_length=100)

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

    name = models.CharField(max_length=200)
    years_of_experience = models.IntegerField()
    skillset = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    cv = models.FileField(upload_to='cvs/')
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
    rejected_by = models.ManyToManyField(Team, related_name='rejected_candidates', blank=True)
    scheduled_time = models.DateTimeField(null=True, blank=True)  # New field to store interview scheduled time

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