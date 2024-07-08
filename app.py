from flask import Flask, render_template, request
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if(request.form['answer'] == ''):
            return "<html><body> <h1>Invalid answer</h1></body></html>"
        else:
            answer = request.form['answer']
            print('test')
            sentences = ["this is a very good sentence", answer]

            model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
            embeddings = model.encode(sentences)
            result = cosine_similarity([embeddings[0]], embeddings[1:])

            return render_template('answer.html', answer=answer, result=result)
    if request.method == 'GET':
        return render_template("index.html")

@app.route('/process_transcription', methods=['POST'])
def process_transcription():
    if request.method == 'POST':
        audio_file = request.files['audio']
        if audio_file:
            try:
                # Use SpeechRecognition to convert audio to text
                recognizer = sr.Recognizer()
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                # Perform any necessary processing in Flask (e.g., database storage)
                return text  # Return processed text
            except sr.UnknownValueError:
                return 'Speech could not be understood.'
            except sr.RequestError as e:
                return f"Could not request results from Google Speech Recognition service; {e}"
        else:
            return 'No audio file uploaded.'
    return 'Invalid request method'

if __name__ == '__main__':
    app.run(debug=True)