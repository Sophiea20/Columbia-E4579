from sqlalchemy.sql.expression import func
from src.api.content.models import Content, GeneratedContentMetadata
from src.api.engagement.models import Engagement
from src import db
import pandas as pd
from scipy.sparse import csr_matrix
import numpy as np
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity 
import heapq
from src.data_structures.user_based_recommender.data_collector import DataCollector

class UserBasedRecommender:

    _instance = None  # Singleton instance reference

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserBasedRecommender, cls).__new__(cls)
            cls._instance.user_similarity_map = {}
            cls._instance.gather_data()
            cls._instance.compute_similarity()
        return cls._instance

    def gather_data(self):
        # Connect to the database and fetch user-content engagement.
        self.interactions_df = DataCollector().get_data_df()
        #we only get 100000 data but can get more/all

    def aggregate_engagement(self, group):
        #summing millisecond engagement values
        millisecond_engagement_sum = group.loc[group['engagement_type'] != 'Like', 'engagement_value'].sum()
        
        # Counting likes and dislikes
        #likes_count = group.loc[(group['engagement_type'] == 'Like') & (group['engagement_value'] == 1)].shape[0]
        #dislikes_count = group.loc[(group['engagement_type'] == 'Like') & (group['engagement_value'] == -1)].shape[0]
        
        return pd.Series({
            'millisecond_engagement_sum': millisecond_engagement_sum,
            #'likes_count': likes_count,
            #'dislikes_count': dislikes_count
        })    
        
    def compute_similarity(self):
        # Compute the similarity between users.
        # For simplicity, we'll use cosine similarity as our metric.
        # Update self.user_similarity_map with the similarities.
        
        TOP_CONTENT = 251
        interactions_df = self.interactions_df

        # Get the top N content based on engagement count
        top_n_content = (interactions_df.groupby('content_id')['engagement_value']
                         .count().nlargest(TOP_CONTENT).index)

        # Filter interactions_df for top content 
        filtered_df = interactions_df[interactions_df['content_id'].isin(top_n_content)]

        # Aggregate engagement
        engagement_aggregate = (filtered_df.groupby(['user_id', 'content_id'])
                                .agg(millisecond_engagement_sum=pd.NamedAgg(
                                    column='engagement_value', aggfunc='sum'))
                                .reset_index())

        # Create a pivot table to get engagement sum for each user and content
        user_content_pivot = (engagement_aggregate.pivot(index='user_id', columns='content_id',
                                                         values='millisecond_engagement_sum')
                              .fillna(0))

        # Convert the pivot table to a sparse matrix
        user_content_sparse = csr_matrix(user_content_pivot)

        # Cosine similarity computation
        user_similarity = cosine_similarity(user_content_sparse)
        SIMILAR_USERS = 20

        # Get user_id to index mapping for easy lookup
        user_idx_dict = {idx: user_id for idx, user_id in enumerate(user_content_pivot.index)}

        # Finding top similar users
        for user_idx, similarities in enumerate(user_similarity):
            user_id = user_idx_dict[user_idx]
            top_similar = heapq.nlargest(SIMILAR_USERS + 1, enumerate(similarities), key=lambda x: x[1])
            self.user_similarity_map[user_id] = [user_idx_dict[idx] for idx, _ in top_similar if idx != user_idx]

    def get_similar_users(self, user_id):
        # Fetch the list of similar users for a given user_id from the map.
        return self.user_similarity_map.get(user_id, [])

    def recommend_items(self, user_id, num_recommendations=10):
        # For a given user, fetch the list of similar users.
        # Recommend items engaged by those users, which the given user hasn't seen.
        
        #can store this df in compute similarity as a class field
        interactions_df = self.interactions_df
        similar_users = self.get_similar_users(user_id)
        content_dict = {}
        seen_content_ids = interactions_df[interactions_df["user_id"] == user_id]["content_id"].unique()

        for similar_user_id in similar_users:
            content_id_list = interactions_df[interactions_df["user_id"] == similar_user_id]["content_id"].unique()
            for content_id in content_id_list:
                if content_id not in seen_content_ids:
                    if content_id in content_dict:
                        content_dict[content_id] += 1
                    else:
                        content_dict[content_id] = 1

        #currently, we order items based on the number of similar users who have engaged with them
        top_items_tuples = heapq.nlargest(num_recommendations, content_dict.items(), key=lambda x:x[1])
        top_items = [item[0] for item in top_items_tuples]
        top_item_scores = [item[1] for item in top_items_tuples]

        #maybe add a solution in case we couldn't generate enough unseen content => increase top users limit

        return top_items, top_item_scores
        
