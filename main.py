from flask import Flask, request, render_template_string, session
import requests
import re

app = Flask(__name__)
app.secret_key = "super_secret_key_123"


# -------------------------
# Extract lesson ID
# -------------------------
def get_url_params(url):
    match = re.search(r'/lesson/([^?#/]+)', url)
    if match:
        return {'id': match.group(1)}
    return {'id': None}


# -------------------------
# Fetch responses
# -------------------------
def fetch_responses(questions):
    responses = []
    for question in questions:
        question_id = question['key']
        try:
            response_url = f"https://cms.quill.org/questions/{question_id}/responses"
            response = requests.get(response_url)
            data = response.json()

            if isinstance(data, list) and data:
                responses.append(data[0].get("text", "Error fetching response"))
            else:
                responses.append("Error fetching response")

        except:
            responses.append("Error fetching response")

    return responses


# -------------------------
# Fetch lesson JSON
# -------------------------
def fetch_lesson_data(url):
    params = get_url_params(url)
    lesson_id = params.get('id')

    if lesson_id:
        json_url = f"https://www.quill.org/api/v1/lessons/{lesson_id}.json"
        try:
            response = requests.get(json_url)
            data = response.json()
            questions = data.get("questions", [])
            responses = fetch_responses(questions)
            return questions, responses
        except:
            return [], []

    return [], []


# -------------------------
# HTML TEMPLATE
# -------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Quille</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: radial-gradient(circle at top, #1b1b1b, #0d0d0d);
            color: #f1f1f1;
            margin: 0;
            padding: 0;
        }
        .box {
            max-width: 650px;
            margin: 60px auto;
            background: #151515;
            padding: 30px;
            border-radius: 14px;
            box-shadow: 0 0 20px #000, inset 0 0 10px #222;
        }
        h2 {
            text-align: center;
            margin-bottom: 25px;
            font-weight: 600;
            letter-spacing: 1px;
        }
        label { font-size: 14px; opacity: 0.9; }
        input, select, textarea, button {
            width: 100%;
            padding: 12px;
            margin-top: 6px;
            margin-bottom: 18px;
            border-radius: 8px;
            font-size: 15px;
        }
        input, select, textarea {
            border: 1px solid #333;
            background: #1e1e1e;
            color: #eee;
        }
        button {
            background: #7c3cff;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: bold;
            transition: 0.2s;
        }
        button:hover {
            background: #692ed6;
        }
        textarea {
            height: 160px;
            resize: vertical;
        }
    </style>
</head>
<body>

<div class="box">
    <h2>Quille</h2>

    <form method="POST">
        <label>Quill Lesson URL</label>
        <input type="text" name="url" value="{{ url }}">

        <button type="submit" name="action" value="load">Load Lesson</button>

        {% if questions %}
            <label>Select Question</label>
            <select name="index">
                {% for q in questions %}
                    <option value="{{ loop.index0 }}" {% if selected_index == loop.index0 %}selected{% endif %}>
                        {{ loop.index }} - {{ q }}
                    </option>
                {% endfor %}
            </select>

            <button type="submit" name="action" value="show">Show Answer</button>
        {% endif %}
    </form>

    {% if answer %}
        <label>Answer</label>
        <textarea readonly>{{ answer }}</textarea>
    {% endif %}
</div>

</body>
</html>
"""


# -------------------------
# Main Route
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    url = session.get("url", "")
    questions = session.get("questions", [])
    responses = session.get("responses", [])
    selected_index = 0
    answer = ""

    if request.method == "POST":
        action = request.form.get("action")
        url = request.form.get("url", url)

        # Load lesson
        if action == "load" and url:
            qs, rs = fetch_lesson_data(url)
            questions = [q["key"] for q in qs]

            # Save to session
            session["questions"] = questions
            session["responses"] = rs
            session["url"] = url

        # Show answer
        elif action == "show":
            questions = session.get("questions", [])
            responses = session.get("responses", [])
            selected_index = int(request.form.get("index", 0))

            if responses:
                answer = responses[selected_index]

    return render_template_string(
        HTML,
        url=url,
        questions=questions,
        selected_index=selected_index,
        answer=answer
    )


if __name__ == "__main__":
    app.run(debug=True)
