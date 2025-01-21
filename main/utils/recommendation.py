from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from main.models import Article
import pandas as pd

def get_recommendations(user_profile):
    articles = Article.objects.all()
    df = pd.DataFrame(list(articles.values()))

    # Preprocess combined features
    df['combined_features'] = (
        df['title'] + ' ' + df['tags'] + ' ' + df['topic'] + ' ' + df['author']
    )

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(df['combined_features'])

    # Calculate similarity
    profile_vector = vectorizer.transform([user_profile])
    similarity_scores = cosine_similarity(profile_vector, tfidf_matrix).flatten()

    # Add scores to DataFrame and sort
    df['similarity_score'] = similarity_scores
    recommendations = df.sort_values(by='similarity_score', ascending=False).head(10)
    return recommendations
