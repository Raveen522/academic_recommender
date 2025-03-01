from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from main.models import Article
import pandas as pd

def get_recommendations(user_profile):
    articles = Article.objects.all()
    df = pd.DataFrame(list(articles.values()))

    # Ensure all text fields are converted to strings and handle missing values
    df = df.fillna('')

    # Combine features, including the new 'content' field
    df['combined_features'] = (
        df['title'] + ' ' + df['tags'] + ' ' + df['topic'] + ' ' + df['author'] + ' ' + df['content']
    )

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(stop_words='english', max_features=7000)  # Increased feature limit for better representation
    tfidf_matrix = vectorizer.fit_transform(df['combined_features'])

    # Transform user profile
    profile_vector = vectorizer.transform([user_profile])

    # Calculate similarity
    similarity_scores = cosine_similarity(profile_vector, tfidf_matrix).flatten()

    # Add scores to DataFrame and sort by similarity
    df['similarity_score'] = similarity_scores
    recommendations = df.sort_values(by='similarity_score', ascending=False).head(10)

    return recommendations
