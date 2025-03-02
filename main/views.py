from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth.decorators import login_required
# from main.utils.recommendation import get_recommendations

# Login view
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "main/login.html")

# Signup view
def signup_view(request):
    if request.method == "POST":
        # Retrieve form data
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        birthday = request.POST['birthday']
        gender = request.POST['gender']
        email = request.POST['email']
        password = request.POST['password']

        # Check if username already exists
        if not User.objects.filter(username=username).exists():
            # Create the user
            user = User.objects.create_user(username=username, email=email, password=password)

            # Create the profile with additional fields
            UserProfile.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                birthday=birthday,
                gender=gender,
                email=email
            )

            # Authenticate and log in the user
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)  # Log the user in

                # Redirect to the interest selection page
                return redirect('interest_selection')  # Replace with the actual URL name
        
        # Handle case where username already exists (optional)
        else:
            return render(request, "main/signup.html", {"error": "Username already exists"})
    
    # Render signup form
    return render(request, "main/signup.html")

# Interest selection view
@login_required
def interest_selection_view(request):
    if request.method == 'POST':
        # Retrieve and save user interests
        interests = request.POST.getlist('interests')
        profile = request.user.profile  # Get the logged-in user's profile
        profile.interests = ", ".join(interests)
        profile.save()

        # Redirect to the next page (e.g., home page or dashboard)
        return redirect('dashboard')  # Replace with the actual URL name
    
    return render(request, 'main/interest_selection.html')

# Dashboard view
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Article, UserProfile, UserReaction
from django.views.decorators.csrf import csrf_exempt
from .utils.recommendation import get_hybrid_recommendations

@login_required
def dashboard_view(request):
    if request.method == "POST" and "logout" in request.POST:
        logout(request)
        return redirect("login")
    
    user_profile = request.user.profile
    user_interests = user_profile.interests.split(',')
    recommendations = get_hybrid_recommendations(user_profile)

    # recommendations = Article.objects.all()  # Replace with actual recommendation logic

    # Fetch user reactions (ratings) for the logged-in user
    user_ratings = {reaction.article.id: reaction.rating for reaction in UserReaction.objects.filter(user_profile=user_profile)}

    articles = Article.objects.filter(id__in=recommendations)

    for article in articles:
        article.rating = user_ratings.get(article.id, 0)  # Default to 0 if no rating
        article.tags_list = article.tags.split(',') if article.tags else []

    return render(request, "main/dashboard.html", {
        "user": request.user,
        "first_name": user_profile.first_name,
        "interests": user_interests,
        "recommendations": articles,  # Pass the actual Article objects
    })


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def react_to_article(request):
    if request.method == "POST":
        article_id = request.POST.get('article_id')
        rating = request.POST.get('rating')  # 1 to 5

        try:
            article = Article.objects.get(id=article_id)
            user_profile = request.user.profile

            # Update or create the rating
            user_reaction, created = UserReaction.objects.update_or_create(
                user_profile=user_profile,
                article=article,
                defaults={'rating': int(rating)}
            )

            return JsonResponse({"success": True, "rating": user_reaction.rating})
        except Article.DoesNotExist:
            return JsonResponse({"success": False, "error": "Article not found"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})
