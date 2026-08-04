import uuid

from builders.main_builder import build_main_agent


class EngineeringStack:

    def __init__(self):
        self.agent = build_main_agent()

    def invoke(self, message: str, thread_id: str | None = None):
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        return self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )