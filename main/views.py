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
from django.db.models import Q


@login_required
def dashboard_view(request):
    if request.method == "POST" and "logout" in request.POST:
        logout(request)
        return redirect("login")

    user_profile = request.user.profile
    user_interests = user_profile.interests.split(',')

    # Get recommended articles (excluding interacted ones)
    recommended_ids = get_hybrid_recommendations(user_profile)
    recommended_articles = Article.objects.filter(id__in=recommended_ids)

    # Fetch user ratings (interacted articles)
    user_reactions = UserReaction.objects.filter(user_profile=user_profile)
    history_articles = [reaction.article for reaction in user_reactions]

    # Assign ratings to articles
    user_ratings = {reaction.article.id: reaction.rating for reaction in user_reactions}
    
    for article in recommended_articles:
        article.rating = user_ratings.get(article.id, 0)
        article.tags_list = article.tags.split(',') if article.tags else []

    for article in history_articles:
        article.rating = user_ratings.get(article.id, 0)
        article.tags_list = article.tags.split(',') if article.tags else []

    # Search Feature
    query = request.GET.get('q', '')
    search_results = []
    search_active = False  # Default to Recommendations Tab

    if query:
        search_results = Article.objects.filter(
            Q(title__icontains=query) |
            Q(tags__icontains=query) |
            Q(topic__icontains=query) |
            Q(author__icontains=query) |
            Q(subject__icontains=query)
        ).distinct()
        search_active = True  # Activate the Search Results Tab

    # Insights Data
    total_articles_read = len(history_articles)
    total_reading_time = sum([article.read_time for article in history_articles])
    avg_reading_time = total_reading_time / total_articles_read if total_articles_read > 0 else 0
    total_ratings_given = len(user_reactions)
    engagement_score = total_reading_time * total_ratings_given  

    # Count articles read per subject
    subject_counts = {}
    for article in history_articles:
        subject_counts[article.subject] = subject_counts.get(article.subject, 0) + 1

    most_read_subject = max(subject_counts, key=subject_counts.get, default="N/A")
    max_subject_reads = subject_counts.get(most_read_subject, 0)

    # Convert subject count to lists for graph plotting
    subjects = list(subject_counts.keys())
    subject_read_counts = list(subject_counts.values())

    # Ratings distribution
    rating_counts = {i: 0 for i in range(1, 6)} 
    for reaction in user_reactions:
        rating_counts[reaction.rating] += 1

    rating_counts_list = list(rating_counts.values())

    # Radar Chart Data (Interest Profile)
    radar_chart_data = {interest: subject_counts.get(interest, 0) / max_subject_reads if max_subject_reads > 0 else 0 for interest in subjects}

    # Convert Interest Profile to lists for graph plotting
    radar_Labels = list(radar_chart_data.keys())
    radar_Values = list(radar_chart_data.values())

    return render(request, "main/dashboard.html", {
        "user": request.user,
        "first_name": user_profile.first_name,
        "interests": user_interests,
        "recommendations": recommended_articles,
        "history": history_articles,
        "search_results": search_results,  # Search results for the Search Results tab
        "query": query,  # Pass the search query back to the template
        "search_active": search_active,  # Indicates if search tab should be active
        # Insights Data
        "total_articles_read": total_articles_read,
        "total_reading_time": total_reading_time,
        "avg_reading_time": avg_reading_time,
        "total_ratings_given": total_ratings_given,
        "engagement_score": engagement_score,
        "most_read_subject": most_read_subject,
        "max_subject_reads": max_subject_reads,
        "subjects": subjects,
        "subject_read_counts": subject_read_counts,
        "rating_counts": rating_counts,
        "rating_counts_list": rating_counts_list,
        "radar_chart_data": radar_chart_data,
        "radar_Labels": radar_Labels,
        "radar_Values": radar_Values,
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
