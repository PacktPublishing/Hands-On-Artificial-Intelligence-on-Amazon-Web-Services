"use strict";

const serverUrl = "http://127.0.0.1:8000";

async function uploadImage() {
    // encode input file as base64 string for upload
    let file = document.getElementById("file").files[0];
    let converter = new Promise(function(resolve, reject) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result
            .toString().replace(/^data:(.*,)?/, ''));
        reader.onerror = (error) => reject(error);
    });
    let encodedString = await converter;

    // clear file upload input field
    document.getElementById("file").value = "";

    // make server call to upload image
    // and return the server upload promise
    return fetch(serverUrl + "/images", {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({filename: file.name, filebytes: encodedString})
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function updateImage(image) {
    document.getElementById("view").style.display = "block";

    let imageElem = document.getElementById("image");
    imageElem.src = image["fileUrl"];
    imageElem.alt = image["fileId"];

    return image;
}

function extractInformation(image) {
    // make server call to extract information
    // and return the server upload promise
    return fetch(serverUrl + "/images/" + image["fileId"] + "/extract-info", {
        method: "POST"
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function populateFields(extractions) {
    let fields = ["name", "title", "email", "phone", "organization", "address", "city", "state", "zip"];
    fields.map(function(field) {
        if (field in extractions) {
            let element = document.getElementById(field);
            element.value = extractions[field].join(" ");
        }
        return field;
    });
    let saveBtn = document.getElementById("save");
    saveBtn.disabled = false;
}

function uploadAndExtract() {
    uploadImage()
        .then(image => updateImage(image))
        .then(image => extractInformation(image))
        .then(translations => populateFields(translations))
        .catch(error => {
            alert("Error: " + error);
        })
}

function saveContact() {
    let contactInfo = {};

    let fields = ["name", "title", "email", "phone", "organization", "address", "city", "state", "zip"];
    fields.map(function(field) {
        let element = document.getElementById(field);
        if (element && element.value) {
            contactInfo[field] = element.value;
        }
        return field;
    });
    let imageElem = document.getElementById("image");
    contactInfo["image"] = imageElem.src;

    // make server call to save contact
    return fetch(serverUrl + "/contacts", {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(contactInfo)
    }).then(response => {
        if (response.ok) {
            clearContact();
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function clearContact() {
    let fields = ["name", "title", "email", "phone", "organization", "address", "city", "state", "zip"];
    fields.map(function(field) {
        let element = document.getElementById(field);
        element.value = "";
        return field;
    });

    let imageElem = document.getElementById("image");
    imageElem.src = "";
    imageElem.alt = "";

    let saveBtn = document.getElementById("save");
    saveBtn.disabled = true;
}

function retrieveContacts() {
    // make server call to get all contacts
    return fetch(serverUrl + "/contacts", {
        method: "GET"
    }).then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new HttpError(response);
        }
    })
}

function displayContacts(contacts) {
    let contactsElem = document.getElementById("contacts")
    while (contactsElem.firstChild) {
        contactsElem.removeChild(contactsElem.firstChild);
    }

    for (let i = 0; i < contacts.length; i++) {
        let contactElem = document.createElement("div");
        contactElem.style = "float: left; width: 50%";
        contactElem.appendChild(document.createTextNode(contacts[i]["name"]));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode(contacts[i]["title"]));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode(contacts[i]["organization"]));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode(contacts[i]["address"]));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode(
             contacts[i]["city"] + ", " + contacts[i]["state"] + " " + contacts[i]["zip"]
        ));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode("phone: " + contacts[i]["phone"]));
        contactElem.appendChild(document.createElement("br"));
        contactElem.appendChild(document.createTextNode("email: " + contacts[i]["email"]));

        let cardElem = document.createElement("div");
        cardElem.style = "float: right; width: 50%";
        let imageElem = document.createElement("img");
        imageElem.src = contacts[i]["image"];
        imageElem.height = "150";
        cardElem.appendChild(imageElem);

        contactsElem.appendChild(document.createElement("hr"));
        contactsElem.appendChild(contactElem);
        contactsElem.appendChild(imageElem);
        contactsElem.appendChild(document.createElement("hr"));
    }
}

function retrieveAndDisplayContacts() {
    retrieveContacts()
        .then(contacts => displayContacts(contacts))
        .catch(error => {
            alert("Error: " + error);
        })
}

class HttpError extends Error {
    constructor(response) {
        super(`${response.status} for ${response.url}`);
        this.name = "HttpError";
        this.response = response;
    }
}
