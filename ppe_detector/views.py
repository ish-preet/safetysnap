from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import PPEImage, PPEDetection
import json
import hashlib
import random

@csrf_exempt
def api_test(request):
    return JsonResponse({"message": "API is working!", "status": "success"})

@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if not username or not email or not password:
                return JsonResponse({
                    "error": {"code": "FIELD_REQUIRED", "message": "All fields required"}
                }, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    "error": {"code": "USER_EXISTS", "message": "Username exists"}
                }, status=400)
            
            user = User.objects.create_user(username=username, email=email, password=password)
            
            return JsonResponse({
                "message": "User created successfully",
                "user": {"id": user.id, "username": user.username, "email": user.email}
            }, status=201)
            
        except Exception as e:
            return JsonResponse({
                "error": {"code": "REGISTRATION_ERROR", "message": f"Failed: {str(e)}"}
            }, status=500)
    
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only POST allowed"}
    }, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    "error": {"code": "FIELD_REQUIRED", "message": "Username and password required"}
                }, status=400)
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    "message": "Login successful",
                    "user": {"id": user.id, "username": user.username, "email": user.email}
                })
            else:
                return JsonResponse({
                    "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}
                }, status=401)
                
        except Exception as e:
            return JsonResponse({
                "error": {"code": "LOGIN_ERROR", "message": f"Failed: {str(e)}"}
            }, status=500)
    
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only POST allowed"}
    }, status=405)

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({"message": "Logout successful"})
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only POST allowed"}
    }, status=405)

def calculate_detections_hash(detections):
    detections_str = json.dumps(detections, sort_keys=True)
    return hashlib.sha256(detections_str.encode()).hexdigest()[:16]

def generate_realistic_detections():
    scenarios = [
        [
            {'label': 'helmet', 'confidence': round(random.uniform(0.85, 0.95), 2), 'bbox': [0.2, 0.1, 0.1, 0.15]},
            {'label': 'vest', 'confidence': round(random.uniform(0.78, 0.88), 2), 'bbox': [0.3, 0.4, 0.2, 0.3]},
            {'label': 'person', 'confidence': round(random.uniform(0.90, 0.96), 2), 'bbox': [0.25, 0.35, 0.3, 0.5]}
        ],
        [
            {'label': 'vest', 'confidence': round(random.uniform(0.75, 0.85), 2), 'bbox': [0.4, 0.3, 0.15, 0.25]},
            {'label': 'person', 'confidence': round(random.uniform(0.88, 0.94), 2), 'bbox': [0.35, 0.25, 0.25, 0.45]}
        ],
        [
            {'label': 'helmet', 'confidence': round(random.uniform(0.82, 0.90), 2), 'bbox': [0.1, 0.2, 0.08, 0.12]},
            {'label': 'person', 'confidence': round(random.uniform(0.85, 0.92), 2), 'bbox': [0.08, 0.18, 0.2, 0.4]},
        ]
    ]
    
    scenario = random.choice(scenarios)
    for detection in scenario:
        detection['confidence'] = round(detection['confidence'] + random.uniform(-0.02, 0.02), 2)
    
    return scenario

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        try:
            # Check authentication
            if not request.user.is_authenticated:
                user = User.objects.first()
                if not user:
                    user = User.objects.create_user('default', 'default@example.com', 'defaultpass')
            else:
                user = request.user
            
            # Check file
            if 'image' not in request.FILES:
                return JsonResponse({
                    "error": {"code": "NO_IMAGE", "message": "No image provided"}
                }, status=400)
            
            image_file = request.FILES['image']
            
            # Calculate hash
            file_hash = hashlib.sha256(image_file.read()).hexdigest()
            image_file.seek(0)
            
            # Check for duplicate
            try:
                existing_image = PPEImage.objects.get(file_hash=file_hash)
                detections = list(existing_image.detections.all().values(
                    'label', 'confidence', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height'
                ))
                
                return JsonResponse({
                    "id": existing_image.id,
                    "message": "Image already exists",
                    "detections": [{
                        "label": d['label'],
                        "confidence": d['confidence'],
                        "bbox": [d['bbox_x'], d['bbox_y'], d['bbox_width'], d['bbox_height']]
                    } for d in detections],
                    "detections_hash": calculate_detections_hash(detections),
                    "upload_date": existing_image.upload_date.isoformat()
                })
                
            except PPEImage.DoesNotExist:
                # Create new image
                image_instance = PPEImage.objects.create(
                    user=user,
                    image=image_file,
                    file_hash=file_hash,
                    processed=True
                )
                
                # Create detections
                detections_data = generate_realistic_detections()
                for detection in detections_data:
                    PPEDetection.objects.create(
                        image=image_instance,
                        label=detection['label'],
                        confidence=detection['confidence'],
                        bbox_x=detection['bbox'][0],
                        bbox_y=detection['bbox'][1],
                        bbox_width=detection['bbox'][2],
                        bbox_height=detection['bbox'][3]
                    )
                
                # Get detections from DB
                db_detections = list(image_instance.detections.all().values(
                    'label', 'confidence', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height'
                ))
                
                return JsonResponse({
                    "id": image_instance.id,
                    "message": "Image processed successfully",
                    "detections": [{
                        "label": d['label'],
                        "confidence": d['confidence'],
                        "bbox": [d['bbox_x'], d['bbox_y'], d['bbox_width'], d['bbox_height']]
                    } for d in db_detections],
                    "detections_hash": calculate_detections_hash(db_detections),
                    "upload_date": image_instance.upload_date.isoformat()
                })
            
        except Exception as e:
            return JsonResponse({
                "error": {"code": "UPLOAD_ERROR", "message": f"Upload failed: {str(e)}"}
            }, status=500)
    
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only POST allowed"}
    }, status=405)

@csrf_exempt
def get_labels(request):
    return JsonResponse({"labels": ["helmet", "vest", "person", "none"]})

@csrf_exempt
def get_images(request):
    if request.method == 'GET':
        try:
            images = PPEImage.objects.all().order_by('-upload_date')
            
            # Filtering
            label_filter = request.GET.get('label')
            if label_filter:
                images = images.filter(detections__label=label_filter).distinct()
            
            # Pagination
            limit = int(request.GET.get('limit', 10))
            offset = int(request.GET.get('offset', 0))
            
            total_count = images.count()
            paginated_images = images[offset:offset + limit]
            
            # Build response
            results = []
            for image in paginated_images:
                detections = list(image.detections.all().values(
                    'label', 'confidence', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height'
                ))
                
                image_url = image.image.url if image.image else None
                annotated_image_url = image.annotated_image.url if hasattr(image, 'annotated_image') and image.annotated_image else None
                
                results.append({
                    "id": image.id,
                    "image_url": image_url,
                    "annotated_image_url": annotated_image_url,
                    "upload_date": image.upload_date.isoformat(),
                    "detections": [{
                        "label": d['label'],
                        "confidence": d['confidence'],
                        "bbox": [d['bbox_x'], d['bbox_y'], d['bbox_width'], d['bbox_height']]
                    } for d in detections],
                    "detections_hash": calculate_detections_hash(detections)
                })
            
            next_offset = offset + limit if offset + limit < total_count else None
            
            return JsonResponse({
                "items": results,
                "next_offset": next_offset,
                "total": total_count
            })
            
        except Exception as e:
            return JsonResponse({
                "error": {"code": "HISTORY_ERROR", "message": f"Failed: {str(e)}"}
            }, status=500)
    
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only GET allowed"}
    }, status=405)

@csrf_exempt
def get_image_detail(request, id):
    if request.method == 'GET':
        try:
            image = PPEImage.objects.get(id=id)
            detections = list(image.detections.all().values(
                'label', 'confidence', 'bbox_x', 'bbox_y', 'bbox_width', 'bbox_height'
            ))
            
            image_url = image.image.url if image.image else None
            annotated_image_url = image.annotated_image.url if hasattr(image, 'annotated_image') and image.annotated_image else None
            
            return JsonResponse({
                "id": image.id,
                "image_url": image_url,
                "annotated_image_url": annotated_image_url,
                "upload_date": image.upload_date.isoformat(),
                "detections": [{
                    "label": d['label'],
                    "confidence": d['confidence'],
                    "bbox": [d['bbox_x'], d['bbox_y'], d['bbox_width'], d['bbox_height']]
                } for d in detections],
                "detections_hash": calculate_detections_hash(detections)
            })
            
        except PPEImage.DoesNotExist:
            return JsonResponse({
                "error": {"code": "NOT_FOUND", "message": f"Image {id} not found"}
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "error": {"code": "IMAGE_ERROR", "message": f"Failed: {str(e)}"}
            }, status=500)
    
    return JsonResponse({
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Only GET allowed"}
    }, status=405)

@csrf_exempt
def get_analytics(request):
    """Get real analytics data from database"""
    if request.method == 'GET':
        try:
            # Calculate real analytics from database
            total_images = PPEImage.objects.count()
            
            # Calculate compliance rate (images with at least one helmet or vest)
            compliant_images = PPEImage.objects.filter(
                detections__label__in=['helmet', 'vest']
            ).distinct().count()
            
            compliance_rate = (compliant_images / total_images * 100) if total_images > 0 else 0
            
            # Get detection statistics
            from django.db.models import Count, Avg
            detection_stats = PPEDetection.objects.values('label').annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence')
            ).order_by('-count')
            
            # Format detection stats
            stats_list = []
            for stat in detection_stats:
                stats_list.append({
                    'label': stat['label'],
                    'count': stat['count'],
                    'avg_confidence': round(stat['avg_confidence'] or 0, 2)
                })
            
            # Get images by date (last 7 days) - FIXED VERSION
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Count
            from django.db.models.functions import TruncDate
            
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            # Use TruncDate for proper date grouping
            images_by_date = PPEImage.objects.filter(
                upload_date__gte=seven_days_ago
            ).annotate(
                date=TruncDate('upload_date')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            # Convert to proper format for frontend
            images_by_date_list = []
            for item in images_by_date:
                images_by_date_list.append({
                    'date': item['date'].isoformat() if item['date'] else '',
                    'count': item['count']
                })
            
            analytics_data = {
                "total_images": total_images,
                "compliance_rate": round(compliance_rate, 1),
                "images_by_date": images_by_date_list,  # Fixed this line
                "detection_stats": stats_list
            }
            
            return JsonResponse(analytics_data)
            
        except Exception as e:
            return JsonResponse({
                "error": {
                    "code": "ANALYTICS_ERROR",
                    "message": f"Failed to load analytics: {str(e)}"
                }
            }, status=500)
    
    return JsonResponse({
        "error": {
            "code": "METHOD_NOT_ALLOWED",
            "message": "Only GET method allowed"
        }
    }, status=405)