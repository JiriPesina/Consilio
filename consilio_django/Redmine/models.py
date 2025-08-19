from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=50)
    createDate = models.DateField()
    parent_id = models.IntegerField(null=True,blank=True,db_column='Parent_ID',help_text='ID nadřazeného projektu')
   

    class Meta:
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
class Issue(models.Model):
    project_id = models.ForeignKey(Project, related_name='issues', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=15)
    status = models.CharField(max_length=15)
    priority = models.CharField(max_length=10)
    assigned = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assigned_issues', on_delete=models.SET_NULL, null=True, blank=True, db_constraint=False,)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
    

class User(AbstractUser):
    API_Key = models.CharField(max_length=50, blank=True, null=True)
    redmine_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    