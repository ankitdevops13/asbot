from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ankit Shakya</title>
  <style>
    /* Background with emoji pattern */
    body {
      margin: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      background: linear-gradient(135deg, #ff00cc, #3333ff);
      background-image: radial-gradient(circle, rgba(255,255,255,0.1) 2px, transparent 2px),
                        linear-gradient(135deg, #ff00cc, #3333ff);
      background-size: 100px 100px;
      font-family: 'Poppins', sans-serif;
      overflow: hidden;
      color: white;
      text-align: center;
      position: relative;
    }

    /* Floating emoji background animation */
    .emoji {
      position: absolute;
      font-size: 2rem;
      opacity: 0.3;
      animation: float 10s infinite ease-in-out;
    }

    @keyframes float {
      0% { transform: translateY(0); }
      50% { transform: translateY(-20px); }
      100% { transform: translateY(0); }
    }

    /* Main glowing name text */
    h1 {
      font-size: 4rem;
      color: #fff;
      text-shadow: 0 0 20px #ff0099, 0 0 40px #ff66cc, 0 0 80px #ff00ff;
      animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
      from { text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff66cc; }
      to { text-shadow: 0 0 30px #ff33cc, 0 0 60px #ff99ff; }
    }

    /* Bottom line */
    footer {
      position: absolute;
      bottom: 15px;
      font-size: 1.2rem;
      color: #fff;
      text-shadow: 0 0 10px #00ffff;
    }
  </style>
</head>
<body>
  <!-- Floating Emojis -->
  <div class="emoji" style="top:10%; left:15%;">🌈</div>
  <div class="emoji" style="top:20%; left:70%;">✨</div>
  <div class="emoji" style="top:60%; left:30%;">🔥</div>
  <div class="emoji" style="top:80%; left:50%;">💫</div>
  <div class="emoji" style="top:40%; left:85%;">💖</div>

  <h1>💎 Ankit Shakya 💎</h1>

  <footer>🤖 Bot made by Ankit Shakya 💜</footer>
</body>
</html>
"""


if __name__ == "__main__":
    app.run()
