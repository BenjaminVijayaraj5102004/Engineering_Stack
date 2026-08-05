"""Simple example demonstrating public EngineeringStack usage."""

from engineeringstack import EngineeringStack

def main():
    stack = EngineeringStack()
    response = stack.invoke("Create a simple Flask hello world endpoint")
    print("Response:", response)

if __name__ == "__main__":
    main()
