document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');
    const progressContainer = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressMessage = document.getElementById('progress-message');
    const progressPercent = document.getElementById('progress-percent');
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('file');
        if (!fileInput.files.length) {
            alert('Please select a file first!');
            return;
        }
        
        startUploadProgress();
        
        const formData = new FormData(uploadForm);
        
        fetch('/bill', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }
            return response.text();
        })
        .then(data => {
            if (typeof data === 'string') {
                document.open();
                document.write(data);
                document.close();
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            hideUploadProgress();
            alert('Upload failed. Please try again.');
            resetUploadButton();
        });
    });
    
    function startUploadProgress() {
        progressContainer.classList.remove('hidden');
        
        uploadBtn.disabled = true;
        uploadBtn.classList.add('loading');
        
        const phases = [
            { percent: 20, message: 'Uploading receipt...', delay: 500 },
            { percent: 45, message: 'Processing image...', delay: 1000 },
            { percent: 70, message: 'Scanning for text...', delay: 1500 },
            { percent: 85, message: 'Extracting total amount...', delay: 800 },
            { percent: 95, message: 'Saving to database...', delay: 600 },
            { percent: 100, message: 'Complete! Redirecting...', delay: 300 }
        ];
        
        let currentPhase = 0;
        
        function updateProgress() {
            if (currentPhase < phases.length) {
                const phase = phases[currentPhase];
                
                setTimeout(() => {
                    progressFill.style.width = phase.percent + '%';
                    progressMessage.textContent = phase.message;
                    progressPercent.textContent = phase.percent + '%';
                    
                    currentPhase++;
                    if (currentPhase < phases.length) {
                        updateProgress();
                    }
                }, currentPhase === 0 ? 0 : phases[currentPhase - 1].delay);
            }
        }
        
        updateProgress();
    }
    
    function hideUploadProgress() {
        progressContainer.classList.add('hidden');
        resetProgress();
    }
    
    function resetProgress() {
        progressFill.style.width = '0%';
        progressMessage.textContent = 'Processing receipt...';
        progressPercent.textContent = '0%';
    }
    
    function resetUploadButton() {
        uploadBtn.disabled = false;
        uploadBtn.classList.remove('loading');
    }
    
    const fileInput = document.getElementById('file');
    const fileText = document.querySelector('.file-text');
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            fileText.textContent = e.target.files[0].name;
        } else {
            fileText.textContent = 'Choose receipt file';
        }
    });
});
