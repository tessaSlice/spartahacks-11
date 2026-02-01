import requests
import json

url = "http://localhost:8080/GetTodos"

payload = {
  "attention_indices" : [
    4,
  ],
  "session_id" : "8109B5DA-6621-4ECE-9CBD-81189FD64A4C",
  "messages" : [
    {
      "speaker" : 1,
      "content" : "Mm-hmm. That's good. What'd you do for work?"
    },
    {
      "content" : " Go to Batman.",
      "speaker" : 2
    },
    {
      "speaker" : 1,
      "content" : " Oh, I do it regularly."
    },
    {
      "speaker" : 2,
      "content" : "Make a calendar event for a meeting with Grant Wang on next friday at 10:00 AM"
    },
    {
      "content" : "Attention",
      "speaker" : 0
    },
    {
      "content" : "Yeah I really need that calendar event created.",
      "speaker" : 2
    },
    {
      "content" : " Also send an email to Grant right? About the thing",
      "speaker" : 1
    },
    {
      "speaker" : 2,
      "content" : " Yeah. The weird thing is I don't know what the thing is."
    },
    {
      "content" : "Attention",
      "speaker" : 0
    },
    {
      "content" : "Actually no, I remember. He needs to come over to my house.",
      "speaker" : 2
    }
  ]
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server. Make sure Flask is running on port 8080.")
except Exception as e:
    print(f"An error occurred: {e}")
