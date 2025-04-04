const video = document.getElementById("video");
const emailInput = document.getElementById("face-login-email");

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        alert("The camera access has been denied " + err.message);
    });

function captureFace() {
    const email = emailInput.value.trim();
    if (!email) {
        alert("Please enter your email address.");
        return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL("image/jpeg");

    fetch("/face-login-admin/", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: new URLSearchParams({
            email: email,
            image: imageData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.message === "Face registered") {
            alert("Success in registration!");
            window.location.href = "/admin/";
        } else if (data.success) {
            alert("Success!");
            window.location.href = "/admin/";
        } else {
            alert("No good!" + data.message);
        }
    })
    .catch(err => {
        alert("An error occured when trying to save the image " + err.message);
    });
}

function getCookie(name) {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith(name + '='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}
