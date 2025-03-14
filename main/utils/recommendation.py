import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Avg
from main.models import Article, UserReaction, UserProfile
from scipy.sparse.linalg import svds

# Weightage for different recommendation methods
WEIGHT_CBF = 0.5
WEIGHT_UBCF = 0.25
WEIGHT_IBCF = 0.25

def get_content_based_recommendations(user_profile, top_n=10):
    """ Content-Based Filtering with fallback to user interests """
    articles = list(Article.objects.all())
    
    if not articles:
        return []

    df = pd.DataFrame([{
        'id': article.id, 
        'title': article.title, 
        'tags': article.tags, 
        'topic': article.topic, 
        'author': article.author
    } for article in articles])

    df['combined_features'] = df['title'] + " " + df['tags'] + " " + df['topic'] + " " + df['author']
    
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined_features'])

    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Find articles rated highly by user
    user_ratings = UserReaction.objects.filter(user_profile=user_profile, rating__gte=4).values_list('article_id', flat=True)
    
    if not user_ratings:
        # Fallback: Recommend trending articles based on user's interests
        user_interests = user_profile.interests.split(", ")  # Assuming interests are stored as a string
        recommended_articles = Article.objects.filter(topic__in=user_interests).order_by('-claps')[:top_n]
        return list(recommended_articles.values_list('id', flat=True))

    user_indices = [df[df['id'] == article_id].index[0] for article_id in user_ratings if article_id in df['id'].values]

    similar_articles = cosine_sim[user_indices].mean(axis=0)
    
    recommendations = sorted(list(enumerate(similar_articles)), key=lambda x: x[1], reverse=True)
    
    recommended_article_ids = [df.iloc[i[0]]['id'] for i in recommendations if df.iloc[i[0]]['id'] not in user_ratings]
    
    return recommended_article_ids[:top_n]


def get_user_based_recommendations(user_profile, top_n=10):
    """ User-Based Collaborative Filtering with fallback to trending articles """
    user_ratings = pd.DataFrame(list(UserReaction.objects.values('user_profile_id', 'article_id', 'rating')))

    if user_ratings.empty or user_ratings['user_profile_id'].nunique() < 2:
        # Fallback: Return trending articles if not enough data
        return list(Article.objects.order_by('-claps')[:top_n].values_list('id', flat=True))

    ratings_matrix = user_ratings.pivot(index='user_profile_id', columns='article_id', values='rating').fillna(0)

    if user_profile.id not in ratings_matrix.index:
        # If user has no ratings, return trending articles
        return list(Article.objects.order_by('-claps')[:top_n].values_list('id', flat=True))

    user_mean = ratings_matrix.mean(axis=1)
    ratings_demeaned = ratings_matrix.sub(user_mean, axis=0)
    
    cosine_sim = cosine_similarity(ratings_demeaned.fillna(0))
    
    user_idx = list(ratings_matrix.index).index(user_profile.id)

    sim_scores = list(enumerate(cosine_sim[user_idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    
    top_users = [ratings_matrix.index[i[0]] for i in sim_scores[1:6]]
    
    top_users_ratings = ratings_matrix.loc[top_users].mean(axis=0)
    unseen_articles = ratings_matrix.loc[user_profile.id] == 0

    recommended_articles = top_users_ratings[unseen_articles].sort_values(ascending=False).index.tolist()

    return recommended_articles[:top_n]


def get_item_based_recommendations(user_profile, top_n=10):
    """ Item-Based Collaborative Filtering with fallback to trending articles """
    user_ratings = pd.DataFrame(list(UserReaction.objects.values('user_profile_id', 'article_id', 'rating')))
    
    if user_ratings.empty or user_ratings['article_id'].nunique() < 2:
        # Fallback: Return trending articles if not enough data
        return list(Article.objects.order_by('-claps')[:top_n].values_list('id', flat=True))

    ratings_matrix = user_ratings.pivot(index='user_profile_id', columns='article_id', values='rating').fillna(0)

    if user_profile.id not in ratings_matrix.index:
        # If user has no ratings, return trending articles
        return list(Article.objects.order_by('-claps')[:top_n].values_list('id', flat=True))

    item_similarity = cosine_similarity(ratings_matrix.T)
    item_similarity_df = pd.DataFrame(item_similarity, index=ratings_matrix.columns, columns=ratings_matrix.columns)
    
    user_articles = UserReaction.objects.filter(user_profile=user_profile).values_list('article_id', flat=True)

    if not user_articles:
        return list(Article.objects.order_by('-claps')[:top_n].values_list('id', flat=True))

    recommended_articles = {}
    
    for article_id in user_articles:
        similar_items = item_similarity_df[article_id].sort_values(ascending=False)
        
        for similar_article, score in similar_items.items():
            if similar_article not in user_articles:
                if similar_article not in recommended_articles:
                    recommended_articles[similar_article] = score
                else:
                    recommended_articles[similar_article] += score

    recommended_articles = sorted(recommended_articles.items(), key=lambda x: x[1], reverse=True)
    recommended_article_ids = [article[0] for article in recommended_articles]

    return recommended_article_ids[:top_n]


def get_hybrid_recommendations(user_profile, top_n=10):
    """ Hybrid Recommendation System with fallbacks """
    cbf_recommendations = get_content_based_recommendations(user_profile, top_n * 2)
    ubcf_recommendations = get_user_based_recommendations(user_profile, top_n * 2)
    ibcf_recommendations = get_item_based_recommendations(user_profile, top_n * 2)

    all_recommendations = cbf_recommendations + ubcf_recommendations + ibcf_recommendations

    if not all_recommendations:
        # Fallback: Recommend the latest trending articles
        return list(Article.objects.order_by('-date_posted')[:top_n].values_list('id', flat=True))

    score_dict = {}

    def add_scores(recommendations, weight):
        for rank, article_id in enumerate(recommendations):
            if article_id not in score_dict:
                score_dict[article_id] = 0
            score_dict[article_id] += (1 / (rank + 1)) * weight  

    add_scores(cbf_recommendations, WEIGHT_CBF)
    add_scores(ubcf_recommendations, WEIGHT_UBCF)
    add_scores(ibcf_recommendations, WEIGHT_IBCF)

    final_recommendations = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    
    recommended_article_ids = [article[0] for article in final_recommendations]

    return recommended_article_ids[:top_n]

