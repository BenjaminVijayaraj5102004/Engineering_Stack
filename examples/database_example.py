"""Database example demonstrating EngineeringStack usage."""

from engineeringstack import EngineeringStack

def main():
    stack = EngineeringStack()
    response = stack.invoke("Design a PostgreSQL schema for a user authentication system with roles")
    print("Database Response:", response)

if __name__ == "__main__":
    main()
