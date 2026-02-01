from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token="")

client.chat_postMessage(
    channel="#all-hackathon",
    text="Hello from Python 👋"
)

result = client.conversations_list()

for ch in result["channels"]:
    print(ch["name"], ch["id"])

history = client.conversations_history(
    channel="#all-hackathon",
    limit=5
)

for msg in history["messages"]:
    print(msg["text"])