from django.contrib import admin
from .models import PPEImage, PPEDetection, IdempotencyKey

@admin.register(PPEImage)
class PPEImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'upload_date', 'processed', 'file_hash_short']
    list_filter = ['upload_date', 'processed']
    search_fields = ['user__username', 'file_hash']
    readonly_fields = ['upload_date']
    
    def file_hash_short(self, obj):
        return obj.file_hash[:16] + '...' if obj.file_hash else ''
    file_hash_short.short_description = 'File Hash'

@admin.register(PPEDetection)
class PPEDetectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'image_id', 'label', 'confidence_percent', 'bbox_display']
    list_filter = ['label']
    search_fields = ['image__id', 'label']
    
    def image_id(self, obj):
        return obj.image.id
    image_id.short_description = 'Image ID'
    
    def confidence_percent(self, obj):
        return f"{obj.confidence * 100:.1f}%"
    confidence_percent.short_description = 'Confidence'
    
    def bbox_display(self, obj):
        return f"[{obj.bbox_x:.3f}, {obj.bbox_y:.3f}, {obj.bbox_width:.3f}, {obj.bbox_height:.3f}]"
    bbox_display.short_description = 'Bounding Box'

@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ['key_short', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    
    def key_short(self, obj):
        return obj.key[:16] + '...' if obj.key else ''
    key_short.short_description = 'Key'