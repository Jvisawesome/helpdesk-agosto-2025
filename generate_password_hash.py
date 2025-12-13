from werkzeug.security import generate_password_hash

if __name__ == "__main__":
    password = input("Enter password to hash: ").strip()
    print(generate_password_hash(password))
