"""API example demonstrating create_engineering_stack usage."""

from engineeringstack import create_engineering_stack

def main():
    agent = create_engineering_stack()
    response = agent.invoke("Build a FastAPI REST endpoint with Pydantic validation")
    print("API Response:", response)

if __name__ == "__main__":
    main()
