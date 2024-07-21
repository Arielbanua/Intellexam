// import {$} from './$.js'


// var SpeechRecognition = window.webkitSpeechRecognition

// var recognition = new SpeechRecognition();

// var textbox = $("#textbox");

// var instructions = $("#instructions");

// var content = '';

// recognition.continuous = true;

// //recognitstion is starrted

// recognition.onstart = function(){
//     instructions.text("recording audio")
// }

// recognition.onspeechend = function(){
//     instructions.text("No Activity")
// }

// recognition.onerror = function(){
//     instructions.text("Try again")
// }

// recognition.onresult = function(event){
//     var current = event.resultIndex;

//     var transcript = event.results[current][0].transcript

//     content += transcript

//     textbox.val(content)
// }

// $("#start-btn").onclick = function(){
//     if(content.length){
//         content += ''
//     }

//     recognition.start();
// }

/*$("#start-btn").click(function(event){
    if(content.length){
        content += ''
    }

    recognition.start();
})*/

















let recognition = null;
let transcript = document.getElementById('transcript');
let recordBtn = document.getElementById('record-btn');
let stopBtn = document.getElementById('stop-btn');

let transcriptText = '';


recordBtn.addEventListener('click', () => {
    if (recognition) {
        recognition.stop();
        recognition = null;
    } else {
        recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-US';
        recognition.maxResults = 10;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onresult = event => {
            let transcriptText = transcript.value;
            for (let i = event.resultIndex; i < event.results.length; i++) {
                transcriptText += event.results[i][0].transcript;
            }
            transcript.value = transcriptText.trim();
        };
        recognition.onstart = () => {
            console.log('Speech recognition started');
        };
        recognition.onend = () => {
            console.log('Speech recognition ended');
            recognition = null;
            recordBtn.disabled = false;
            stopBtn.disabled = true;
        };
        recognition.onerror = event => {
            console.log('Error occurred: ', event.error);
        };
        recognition.start();
        recordBtn.disabled = true;
        stopBtn.disabled = false;

        recognition.onresult = event => {
            for (let i = event.resultIndex; i < event.results.length; i++) {
              if (event.results[i].isFinal) {
                transcriptText += event.results[i][0].transcript;
                break;
              } else {
                transcriptText += event.results[i][0].transcript;
              }
            }
            transcript.value = transcriptText.trim();
          };
    }
});

stopBtn.addEventListener('click', () => {
    if (recognition) {
        recognition.stop();
        recognition = null;
        recordBtn.disabled = false;
        stopBtn.disabled = true;
    }
});