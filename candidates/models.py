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

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'candidates_candidate'