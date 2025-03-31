from .models import UserPreference

def themeMode(request):
    try:
        userPreference = UserPreference.objects.get(user_id=request.user.id)
    except:
        userPreference = None
    return {
        'userPreference': userPreference,
    }