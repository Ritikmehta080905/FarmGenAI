from database.db import Database


def signup_user(data: dict):
    for user in Database.users.values():
        if user["email"] == data["email"]:
            return {"error": "User already exists"}

    user_id = Database.generate_id("user")

    user_record = {
        "user_id": user_id,
        "name": data["name"],
        "email": data["email"],
        "password": data["password"],  # hackathon only
        "location": data["location"],
        "language": data.get("language", "Marathi")
    }

    Database.users[user_id] = user_record
    Database.history[user_id] = []

    Database.farmers[user_id] = {
        "id": user_id,
        "name": data["name"],
        "location": data["location"],
        "language": data.get("language", "Marathi")
    }

    return {
        "user_id": user_id,
        "name": user_record["name"],
        "email": user_record["email"],
        "location": user_record["location"],
        "language": user_record["language"],
        "message": "Signup successful"
    }


def login_user(data: dict):
    for user in Database.users.values():
        if user["email"] == data["email"] and user["password"] == data["password"]:
            return {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"],
                "location": user["location"],
                "language": user["language"],
                "message": "Login successful"
            }

    return {"error": "Invalid email or password"}