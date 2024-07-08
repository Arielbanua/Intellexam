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

if __name__ == '__main__':
    app.run(debug=True)