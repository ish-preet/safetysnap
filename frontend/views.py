from django.shortcuts import render

def index(request):
    """Home page view"""
    return render(request, 'frontend/index.html')

def upload(request):
    """Image upload page view"""
    return render(request, 'frontend/upload.html')

def history(request):
    """Image history page view"""
    return render(request, 'frontend/history.html')

def result(request, id):
    """Result page view for specific image"""
    return render(request, 'frontend/result.html', {'image_id': id})

def analytics(request):
    """Analytics dashboard page view"""
    return render(request, 'frontend/analytics.html')