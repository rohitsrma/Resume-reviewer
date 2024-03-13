from django.db import models

# Create your models here.
class Resume(models.Model):
    uploaded_by = models.CharField(max_length=100)
    upload_date = models.DateTimeField(auto_now_add=True)
    resume_file = models.FileField(upload_to='resumes/')

    def __str__(self):
        return self.uploaded_by + "'s Resume"
