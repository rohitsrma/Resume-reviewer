from rest_framework import serializers
from .models import Resume

class PDFSerializer(serializers.ModelSerializer):
    review_feedback = serializers.CharField(required=False)
    class Meta:
        model = Resume
        fields = ('id', 'resume_file', 'uploaded_by', 'review_feedback')
