import requests
import json

url = "http://localhost:8080/GetTodos"

payload = {
  "attention_indices" : [
    4,
    9,
    14
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
      "content" : "Make a calendar event for a meeting with John Doe on April 1st at 10:00 AM"
    },
    {
      "content" : "Attention",
      "speaker" : 0
    },
    {
      "content" : "w the official, like, game works.",
      "speaker" : 2
    },
    {
      "content" : " No.",
      "speaker" : 1
    },
    {
      "speaker" : 2,
      "content" : " Yeah."
    },
    {
      "speaker" : 1,
      "content" : "Uh, I don't know. They, like, c they, like, sped up the gam"
    },
    {
      "content" : "Attention",
      "speaker" : 0
    },
    {
      "speaker" : 1,
      "content" : " Uh, I don't know. They, like, they, like, sped up the game in mobile games, like, uh,"
    },
    {
      "speaker" : 1,
      "content" : " this, this, uh, this magazine ramps up really quickly."
    },
    {
      "content" : " I have to make sure.",
      "speaker" : 1
    },
    {
      "content" : "No, the problem with the",
      "speaker" : 1
    },
    {
      "speaker" : 0,
      "content" : "Attention"
    },
    {
      "content" : " No, the problem with the, uh, fucking water, but the, the problem with these desktop things is they don't have a magazine in it, so they last game for a few weeks, like, the, the AI just kind of, like, put you to put it in front of you, just, like, mounts a mega blaster and just one-shots all the time.",
      "speaker" : 1
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
