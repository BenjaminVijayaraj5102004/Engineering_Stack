import uuid

from builders.main_builder import build_main_agent


main_agent = build_main_agent()


if __name__ == "__main__":
    print("Executing Main Agent...")

    response = main_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Create a post endpoint in flask."
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": str(uuid.uuid4())
            }
        },
    )

    print(response)