from django.db import models
from django.contrib.auth.models import User

class PPEImage(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    annotated_image = models.ImageField(upload_to='annotated/', null=True, blank=True)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'ppe_images'
    
    def __str__(self):
        return f"Image {self.id} - {self.user.username}"

class PPEDetection(models.Model):
    PPE_LABELS = [
        ('helmet', 'Helmet'),
        ('vest', 'Safety Vest'),
        ('person', 'Person'),
        ('none', 'No PPE'),
    ]
    
    image = models.ForeignKey(PPEImage, on_delete=models.CASCADE, related_name='detections')
    label = models.CharField(max_length=20, choices=PPE_LABELS)
    confidence = models.FloatField()
    bbox_x = models.FloatField()
    bbox_y = models.FloatField()
    bbox_width = models.FloatField()
    bbox_height = models.FloatField()
    
    class Meta:
        db_table = 'ppe_detections'
    
    def __str__(self):
        return f"{self.label} ({self.confidence:.0%})"

class IdempotencyKey(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'idempotency_keys'
    
    def __str__(self):
        return f"Key {self.key[:16]}..."