import {$} from './$.js'


var SpeechRecognition = window.webkitSpeechRecognition

var recognition = new SpeechRecognition();

var textbox = $("#textbox");

var instructions = $("#instructions");

var content = '';

recognition.continuous = true;

//recognitstion is starrted

recognition.onstart = function(){
    instructions.text("recording audio")
}

recognition.onspeechend = function(){
    instructions.text("No Activity")
}

recognition.onerror = function(){
    instructions.text("Try again")
}

recognition.onresult = function(event){
    var current = event.resultIndex;

    var transcript = event.results[current][0].transcript

    content += transcript

    textbox.val(content)
}

$("#start-btn").onclick = function(){
    if(content.length){
        content += ''
    }

    recognition.start();
}

/*$("#start-btn").click(function(event){
    if(content.length){
        content += ''
    }

    recognition.start();
})*/