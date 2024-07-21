if ("webkitSpeechRecognition" in window) {
  const questions = document.querySelectorAll('.speech-recognition-container');

  questions.forEach((questionContainer) => {
      const questionId = questionContainer.querySelector('textarea').name.replace('answer_', '');
      const startButton = questionContainer.querySelector(`#start_${questionId}`);
      const stopButton = questionContainer.querySelector(`#stop_${questionId}`);
      const interimTranscriptElement = questionContainer.querySelector(`#interim_${questionId}`);
      const finalTranscriptElement = questionContainer.querySelector(`#final_${questionId}`);
      const textarea = questionContainer.querySelector(`textarea`);

      let speechRecognition = new webkitSpeechRecognition();
      let finalTranscript = "";
      let interimTranscript = "";

      speechRecognition.continuous = true;
      speechRecognition.interimResults = true;

      speechRecognition.onstart = () => {
          // Show the Status Element
          // document.querySelector("#status").style.display = "block";
      };
      speechRecognition.onerror = () => {
          // Hide the Status Element
          // document.querySelector("#status").style.display = "none";
      };
      speechRecognition.onend = () => {
          // Hide the Status Element
          // document.querySelector("#status").style.display = "none";
      };

      speechRecognition.onresult = (event) => {
          interimTranscript = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                  finalTranscript += event.results[i][0].transcript;
              } else {
                  interimTranscript += event.results[i][0].transcript;
              }
          }

          interimTranscriptElement.innerHTML = interimTranscript;
          finalTranscriptElement.innerHTML = finalTranscript;
          textarea.value = finalTranscript;
      };

      startButton.onclick = () => {
          speechRecognition.start();
      };

      stopButton.onclick = () => {
          speechRecognition.stop();
      };
  });
} else {
  console.log("Speech Recognition Not Available");
}