# Game Rental System with MongoDB

## Introduction
This Python project focuses solely on the SQL aspect of a game rental system, utilizing MongoDB as the NoSQL database. While the project includes a graphical user interface (GUI), it's important to note that our contribution is strictly limited to the backend functionalities, and we did not partake in the development or modification of the GUI itself.
Our role primarily involved implementing user registration, login, game recommendation, and game rental functionalities within the existing framework.

## Project Structure
- `game.py`: Main script to run the game simulation.
- `managers.py`: Contains classes for managing user authentication (`LoginManager`) and database operations (`DBManager`).
- `NintendoGames.csv`: Sample CSV file containing game data.
- `README.md`: Instructions and documentation.

## Functionality
### User Registration
- **Function**: `register_user(username: str, password: str) -> None`
- Registers a new user in the system, hashing the password using bcrypt before storing it securely.
- Validates username and password, ensuring they are not empty and have at least 3 characters.
- Checks for duplicate usernames and raises appropriate errors.

### User Login
- **Function**: `login_user(username: str, password: str) -> object`
- Logs in a user with the provided username and password.
- Validates the provided credentials against the hashed password stored in the database.
- Returns a user object upon successful login.

### Load CSV Data
- **Function**: `load_csv() -> None`
- Loads game data from a CSV file (`NintendoGames.csv`) into the MongoDB collection.
- Ensures data integrity by converting relevant fields and adding necessary fields like `is_rented`.

### Game Recommendation
- **Function**: `recommend_games_by_genre(user: dict) -> str`
- Recommends games based on the genres of games rented by the user.
- Selects genres randomly, taking into account the probability distribution.
- Queries the database to find games with the selected genre and returns top recommendations.

- **Function**: `recommend_games_by_name(user: dict) -> str`
- Recommends games based on the similarity of rented game names.
- Computes TF-IDF vectors for game titles and calculates cosine similarity.
- Returns top recommended game titles based on similarity.

### Game Rental
- **Function**: `rent_game(user: dict, game_title: str) -> str`
- Allows a user to rent a game.
- Checks if the game exists and is not already rented.
- Marks the game as rented and adds it to the user's rented games list.

### Return Game
- **Function**: `return_game(user: dict, game_title: str) -> str`
- Enables a user to return a rented game.
- Removes the game from the user's rented games list and updates its status in the database.

## License
This project is licensed under the MIT License.

