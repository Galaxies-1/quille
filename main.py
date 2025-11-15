from flask import Flask, request, render_template_string
import requests
import re

app = Flask(__name__)

# Function to extract lesson ID from URL
def get_url_params(url):
    match = re.search(r'/lesson/([^?#/]+)', url)
    if match:
        return {'id': match.group(1)}
    return {'id': None}

# Fetch responses for each question
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

# Fetch lesson data
def fetch_lesson_data(url):
    params = get_url_params(url)
    lesson_id = params.get('id')
    if not lesson_id:
        return [], []

    try:
        json_url = f"https://www.quill.org/api/v1/lessons/{lesson_id}.json"
        response = requests.get(json_url)
        data = response.json()

        questions = data.get("questions", [])
        responses = fetch_responses(questions)
        return questions, responses
    except Exception as e:
        print("Error:", e)
        return [], []


# ------------------ FLASK WEB UI ------------------

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
            {% for i, q in enumerate(questions) %}
            <option value="{{ i }}" {% if i == selected %}selected{% endif %}>
                {{ i+1 }} - {{ q.key }}
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


@app.route("/", methods=["GET", "POST"])
def home():
    url = ""
    questions = []
    responses = []
    answer = ""
    selected = 0

    if request.method == "POST":
        url = request.form.get("lesson_url", "")

        questions, responses = fetch_lesson_data(url)

        if "qindex" in request.form:
            selected = int(request.form.get("qindex"))
            if selected < len(responses):
                answer = responses[selected]

    return render_template_string(
        PAGE,
        url=url,
        questions=questions,
        responses=responses,
        answer=answer,
        selected=selected
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
