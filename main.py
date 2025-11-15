from flask import Flask, request, render_template_string
import requests
import re

app = Flask(__name__)

# -----------------------------
# Extract lesson ID from URL
# -----------------------------
def get_url_params(url):
    match = re.search(r'/lesson/([^?#/]+)', url)
    if match:
        return {'id': match.group(1)}
    return {'id': None}

# -----------------------------
# Fetch responses for each question
# -----------------------------
def fetch_responses(questions):
    responses = []
    for question in questions:
        qid = question['key']
        try:
            resp = requests.get(f"https://cms.quill.org/questions/{qid}/responses")
            data = resp.json()
            if isinstance(data, list) and data:
                responses.append(data[0].get("text", "Error fetching response"))
            else:
                responses.append("Error fetching response")
        except:
            responses.append("Error fetching response")
    return responses

# -----------------------------
# Fetch lesson JSON
# -----------------------------
def fetch_lesson_data(url):
    params = get_url_params(url)
    lesson_id = params.get('id')

    if not lesson_id:
        return [], []

    try:
        api_url = f"https://www.quill.org/api/v1/lessons/{lesson_id}.json"
        resp = requests.get(api_url)
        data = resp.json()

        questions = data.get("questions", [])
        responses = fetch_responses(questions)
        return questions, responses
    except Exception as e:
        print("ERROR fetch_lesson_data:", e)
        return [], []


# -----------------------------
# HTML Template (no enumerate)
# -----------------------------
PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Quille Web</title>
    <style>
        body { font-family: Arial; padding: 20px; max-width: 800px; margin: auto; }
        textarea { width: 100%; height: 150px; }
        select { width: 100%; padding: 8px; }
        button { padding: 10px; margin-top: 10px; width: 100%; }
    </style>
</head>
<body>

    <h2>Quille - Web Version</h2>

    <form method="POST">
        <label>Enter Quill Lesson URL:</label><br>
        <input type="text" name="lesson_url" style="width:100%;" value="{{ url }}"><br><br>

        <button type="submit">Load Lesson</button>
    </form>

    {% if questions %}
    <hr>
    <h3>Select a Question:</h3>

    <form method="POST">
        <input type="hidden" name="lesson_url" value="{{ url }}">

        <select name="qindex">
            {% for i, q in questions %}
            <option value="{{ i }}" {% if i == selected %}selected{% endif %}>
                {{ i + 1 }} - {{ q.key }}
            </option>
            {% endfor %}
        </select>

        <button type="submit">Show Answer</button>
    </form>
    {% endif %}

    {% if answer %}
    <hr>
    <h3>Answer:</h3>
    <textarea readonly>{{ answer }}</textarea>
    {% endif %}

</body>
</html>
"""

# -----------------------------
# Flask Homepage Handler
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    url = ""
    questions_raw = []
    responses = []
    answer = ""
    selected = 0
    indexed_questions = []

    if request.method == "POST":
        url = request.form.get("lesson_url", "")

        # Load questions & responses
        questions_raw, responses = fetch_lesson_data(url)

        # Create list of (index, question)
        indexed_questions = list(enumerate(questions_raw))

        # If user selected a question
        if "qindex" in request.form and indexed_questions:
            selected = int(request.form.get("qindex"))
            if selected < len(responses):
                answer = responses[selected]
    else:
        indexed_questions = []

    return render_template_string(
        PAGE,
        url=url,
        questions=indexed_questions,
        responses=responses,
        answer=answer,
        selected=selected
    )


# -----------------------------
# Run app on Render
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
