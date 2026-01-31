# Setting it up

You need to create an `.env` file that contains the Gemini API key:
```
API_KEY="XXX"
```

You need at least 2 terminals:
- in the parent directory of the Flask application you need to run the following command:
```
flask --app spartahack run
```

Then you need to create a new terminal to run the following ngrok application:
```
ngrok http 5000
```

NOTE: you need to be careful which port is being sent in Flask. By default it's set to 5000 but in the code it's set to 8080. Not sure why it's not. 

Then you can run the following POST command to test it via curl:
```
curl -X POST   -H "Content-Type: application/json"   -d "{ \"messages\": [ \
        { \"speaker\": 2, \"content\": \"I mean, I guess I'm not really enforcing it, but given that it'll be, like, it—\" }, \
        { \"speaker\": 2, \"content\": \" Yeah, it's too funny.\" }, \
        { \"speaker\": 1, \"content\": \" Yeah, it kind of has to, yeah.\" }, \
        { \"speaker\": 0, \"content\": \"Attention\" } \
      ], \
      \"attention_indices\": [3], \
      \"session_id\": \"808DE96A-249B-414F-BF1B-8ABE394467F0\" }"   https://unsuited-nonlitigiously-dani.ngrok-free.dev/GetTodos
```

NOTE: ngrok uses HTTPS, but the localhost uses HTTP. This was a bug where I noticed it wasn't actually making the API call.
