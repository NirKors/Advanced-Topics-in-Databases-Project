import pymongo
import bcrypt
import ast
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LoginManager:

    def __init__(self) -> None:
        # MongoDB connection
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["project"]
        self.collection = self.db["users"]
        self.salt = b"$2b$12$ezgTynDsK3pzF8SStLuAPO"  # TODO: if not working, generate a new salt

    def register_user(self, username: str, password: str) -> None:
        # Check if username and password are not empty strings
        if not username or not password:
            raise ValueError("Username and password are required.")

        # Check if username and password are at least 3 characters long
        if len(username) < 3 or len(password) < 3:
            raise ValueError("Username and password must be at least 3 characters.")

        # Check if the username already exists
        if self.collection.find_one({"username": username}):
            raise ValueError(f"User already exists: {username}.")

        # Hash the password using bcrypt
        hashed_pass = bcrypt.hashpw(password.encode(), self.salt)

        # Create a new user
        self.collection.insert_one({"username": username, "password": hashed_pass})

    def login_user(self, username: str, password: str) -> object:
        # Find the user with the provided username
        user = self.collection.find_one({"username": username})

        if user:
            # Check if the provided password matches the hashed password
            if bcrypt.checkpw(password.encode(), user["password"]):
                print(f"Logged in successfully as: {username}")
                return user
            else:
                raise ValueError("Invalid username or password")
        else:
            raise ValueError("Invalid username or password")


class DBManager:

    def __init__(self) -> None:
        # MongoDB connection
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["project"]
        self.user_collection = self.db["users"]
        self.game_collection = self.db["games"]

    def load_csv(self) -> None:
        # Load the CSV
        df = pd.read_csv("NintendoGames.csv")

        # Convert genres field to list
        df['genres'] = df['genres'].apply(ast.literal_eval)

        # Add "is_rented" field with the values False
        df['is_rented'] = False

        # Insert all the records into games collection
        records = df.to_dict(orient='records')

        for record in records:
            unique = {"title": record["title"]}
            self.game_collection.update_many(unique, {"$set": record}, upsert=True)

    def recommend_games_by_genre(self, user: dict) -> str:
        # Get the list of games rented by the user
        user = self.user_collection.find_one({"username": user['username']})

        rented_games_titles = user.get('rented_games', [])
        rented_games = [game['title'] for game in rented_games_titles]

        if not rented_games:
            return "No games rented"

        # Count the occurrences of each genre among the rented games
        genre_count = {}
        for game_title in rented_games:
            game = self.game_collection.find_one({"title": game_title})
            if game:
                for genre in game['genres']:
                    genre_count[genre] = genre_count.get(genre, 0) + 1

        # Calculate the probability distribution for genres
        total_rented_games = len(rented_games)
        genre_probabilities = {genre: count / total_rented_games for genre, count in genre_count.items()}

        # Select a genre randomly based on the probability distribution
        chosen_genre = random.choices(list(genre_probabilities.keys()), weights=list(genre_probabilities.values()))[0]

        # Filter the game collection to not include any games in rented_games
        not_rented_games = list(self.game_collection.find({"title": {"$nin": rented_games}}))

        # Query the filtered game collection to find 5 games with the chosen genre
        recommended_games = [game for game in not_rented_games if chosen_genre in game['genres']]
        if len(recommended_games) > 5:
            recommended_games = random.sample(recommended_games, 5)

        # Return the titles as a string separated with "\n"
        return "\n".join(game["title"] for game in recommended_games)

    def recommend_games_by_name(self, user: dict) -> str:
        # Get the list of games rented by the user
        user = self.user_collection.find_one({"username": user['username']})

        rented_games_titles = user.get('rented_games', [])
        rented_games = [game['title'] for game in rented_games_titles]

        if not rented_games:
            return "No games rented"

        # Choose a random game from the rented games
        chosen_game_title = random.choice(rented_games)

        # Compute TF-IDF vectors for all game titles and the chosen title
        titles = [game['title'] for game in self.game_collection.find()]
        titles.append(chosen_game_title)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(titles)

        # Compute cosine similarity between the TF-IDF vectors of the chosen title and all other games The -1 in
        # tfidf_matrix[-1] simply grabs the last element of the tfidf_matrix. Since the chosen game's vector was
        # added last, this efficiently extracts its representation for similarity calculations with all other games
        # in the matrix.
        cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])

        # Sort the titles based on cosine similarity
        sorted_indices = cosine_similarities.argsort()[0][::-1]
        recommended_games = [titles[i] for i in sorted_indices if titles[i] != rented_games][1:6]


        # Return the top 5 recommended titles as a string separated with "\n"
        return "\n".join(recommended_games)

    def rent_game(self, user: dict, game_title: str) -> str:
        # Query the game collection to find the game with the provided title
        user = self.user_collection.find_one({"username": user['username']})
        game = self.game_collection.find_one({"title": game_title})
        if not game:
            return f"{game_title} not found"

        # Check if the game is not already rented
        if game.get('is_rented', False):
            return f"{game_title} is already rented"

        # Mark the game as rented in the game collection
        self.game_collection.update_one({"title": game_title}, {"$set": {"is_rented": True}})

        # Add the game to the user's rented games list
        self.user_collection.update_one({"username": user.get('username')}, {"$push": {"rented_games": game}})

        return f"{game_title} rented successfully"

    def return_game(self, user: dict, game_title: str) -> str:
        # Get the list of games rented by the user, returns and empty list by default (just in case)
        user = self.user_collection.find_one({"username": user['username']})
        game = self.game_collection.find_one({"title": game_title})
        rented_games_user = user.get('rented_games', [])
        rented_games = [game['title'] for game in rented_games_user]

        # Check if the game with the provided title is rented by the user
        if game_title not in rented_games:
            return f"{game_title} was not rented by you"

        # Remove the game from the user's rented games list
        self.user_collection.update_one({"username": user.get('username')}, {"$pull": {"rented_games": game}})

        # Mark the game as not rented in the game collection
        self.game_collection.update_one({"title": game_title}, {"$set": {"is_rented": False}})

        return f"{game_title} returned successfully"
