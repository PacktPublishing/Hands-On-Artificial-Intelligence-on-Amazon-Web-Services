"use strict";

const serverUrl = "http://127.0.0.1:8000";

class HttpError extends Error {
    constructor(response) {
        super(`${response.status} for ${response.url}`);
        this.name = "HttpError";
        this.response = response;
    }
}

let audioRecorder;
let recordedAudio;

const mediaConstraints = {
    audio: true
};
navigator.getUserMedia(mediaConstraints, onMediaSuccess, onMediaError);

const maxAudioLength = 30000;
let audioFile = {};

function onMediaSuccess(audioStream) {
    audioRecorder = new MediaStreamRecorder(audioStream);
    audioRecorder.mimeType = "audio/wav";
    audioRecorder.ondataavailable = handleAudioData;
}

function onMediaError(error) {
    alert("audio recording not available: " + error.message);
}

function startRecording() {
    recordedAudio = [];
    audioRecorder.start(maxAudioLength);
}

function stopRecording() {
    audioRecorder.stop();
}

function handleAudioData(audioRecording) {
    audioRecorder.stop();

    audioFile = new File([audioRecording], "recorded_audio.wav", {type: "audio/wav"});

    let audioElem = document.getElementById("recording-player");
    audioElem.src = window.URL.createObjectURL(audioRecording);
}

let isRecording = false;

function toggleRecording() {
    let toggleBtn = document.getElementById("record-toggle");
    let translateBtn = document.getElementById("translate");

    if (isRecording) {
        toggleBtn.value = 'Record';
        translateBtn.disabled = false;
        stopRecording();
    } else {
        toggleBtn.value = 'Stop';
        translateBtn.disabled = true;
        startRecording();
    }

    isRecording = !isRecording;
}

async function uploadRecording() {
    // encode recording file as base64 string for upload
    let converter = new Promise(function(resolve, reject) {
        const reader = new FileReader();
        reader.readAsDataURL(audioFile);
        reader.onload = () => resolve(reader.result
            .toString().replace(/^data:(.*,)?/, ''));
        reader.onerror = (error) => reject(error);
    });
    let encodedString = await converter;

    // make server call to upload image
    // and return the server upload promise
    return fetch(serverUrl + "/recordings", {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({filename: audioFile.name, filebytes: encodedString})
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

let fromLang;
let toLang;

function translateRecording(audio) {
    let fromLangElem = document.getElementById("fromLang");
    fromLang = fromLangElem[fromLangElem.selectedIndex].value;
    let toLangElem = document.getElementById("toLang");
    toLang = toLangElem[toLangElem.selectedIndex].value;

    // start translation text spinner
    let textSpinner = document.getElementById("text-spinner");
    textSpinner.hidden = false;

    // make server call to transcribe recorded audio
    return fetch(serverUrl + "/recordings/" + audio["fileId"] + "/translate-text", {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({fromLang: fromLang, toLang: toLang})
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function updateTranslation(translation) {
    // stop translation text spinner
    let textSpinner = document.getElementById("text-spinner");
    textSpinner.hidden = true;

    let transcriptionElem = document.getElementById("transcription");
    transcriptionElem.appendChild(document.createTextNode(translation["text"]));

    let translationElem = document.getElementById("translation");
    translationElem.appendChild(document.createTextNode(translation["translation"]["translatedText"]));

    return translation
}

function synthesizeTranslation(translation) {
    // start translation audio spinner
    let audioSpinner = document.getElementById("audio-spinner");
    audioSpinner.hidden = false;

    // make server call to synthesize translation audio
    return fetch(serverUrl + "/synthesize_speech", {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: translation["translation"]["translatedText"], language: toLang})
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function updateTranslationAudio(audio) {
    // stop translation audio spinner
    let audioSpinner = document.getElementById("audio-spinner");
    audioSpinner.hidden = true;

    let audioElem = document.getElementById("translation-player");
    audioElem.src = audio["audioUrl"];
}

function uploadAndTranslate() {
    let toggleBtn = document.getElementById("record-toggle");
    toggleBtn.disabled = true;
    let translateBtn = document.getElementById("translate");
    translateBtn.disabled = true;

    uploadRecording()
        .then(audio => translateRecording(audio))
        .then(translation => updateTranslation(translation))
        .then(translation => synthesizeTranslation(translation))
        .then(audio => updateTranslationAudio(audio))
        .catch(error => {
            alert("Error: " + error);
        })

    toggleBtn.disabled = false;
}
