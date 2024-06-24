async function sendInstructions() {

    const speed = document.getElementById("speed").value;
    const direction = document.getElementById("direction").value;
    const wheelAngle = document.getElementById('wheelAngle').value;
    const trackId = document.getElementById("trackId").value;


    try {
        const response = await fetch(' https://XYZ.REGION.amazonaws.com/dev', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ speed, direction, wheelAngle, trackId }),
        });

        if (response.ok) {
            document.getElementById("statusMessage").innerText = 'Instructions sent successfully!';
        } else {
            document.getElementById("statusMessage").innerText = 'Failed to send instructions';
        }
    } catch (error) {
        console.error('Error sending instructions:', error);
        document.getElementById("statusMessage").innerText = 'Error sending instructions';
    }
}

async function sendTrack() {

    const send_trackId = document.getElementById("send_trackId").value;

    try {
        const response = await fetch(' https://https://XYZ.REGION.amazonaws.com/dev', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({send_trackId}),
        });

        if (response.ok) {
            document.getElementById("statusMessage2").innerText = 'Track loaded';
        } else {
            document.getElementById("statusMessage2").innerText = 'Track failed to load';
        }
    } catch (error) {
        console.error('Error sending instructions:', error);
        document.getElementById("statusMessage2").innerText = 'Error sending instructions';
    }
}

