// Update speed value display
document.getElementById('speed').addEventListener('input', function() {
    document.getElementById('speedValue').textContent = this.value;
});

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.className = `alert alert-${type} mt-3`;
    statusDiv.textContent = message;
    statusDiv.classList.remove('d-none');
}

// Hide status message
function hideStatus() {
    document.getElementById('statusMessage').classList.add('d-none');
}

// Hide download section
function hideDownload() {
    document.getElementById('downloadSection').classList.add('d-none');
}

// Get form data
function getFormData() {
    return {
        text: document.getElementById('text').value,
        speed: document.getElementById('speed').value,
        voice_type: document.querySelector('input[name="voice_type"]:checked').value
    };
}

// Convert and play audio
async function convertAndPlay() {
    hideDownload();
    const formData = getFormData();
    
    if (!formData.text.trim()) {
        showStatus('Please enter some text to convert', 'warning');
        return;
    }

    showStatus('Converting text to speech...', 'info');
    
    try {
        const response = await fetch('/convert-play', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Conversion failed');
        
        const blob = await response.blob();
        const audio = new Audio(URL.createObjectURL(blob));
        audio.addEventListener('ended', () => {
            hideStatus();
        });
        audio.play();
        
        showStatus('Playing audio...', 'success');
    } catch (error) {
        showStatus('Failed to convert text to speech: ' + error.message, 'danger');
    }
}

// Generate and download audio
async function generateAudio() {
    hideDownload();
    const formData = getFormData();
    
    if (!formData.text.trim()) {
        showStatus('Please enter some text to convert', 'warning');
        return;
    }

    showStatus('Generating audio file...', 'info');
    
    try {
        const response = await fetch('/generate-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Generation failed');
        
        const blob = await response.blob();
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = 'tts_output.wav';
        
        downloadLink.addEventListener('click', () => {
            setTimeout(hideStatus, 2000);
        });
        
        document.getElementById('downloadSection').classList.remove('d-none');
        showStatus('Audio file generated successfully!', 'success');
    } catch (error) {
        showStatus('Failed to generate audio file: ' + error.message, 'danger');
    }
}