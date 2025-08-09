document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const fileText = document.querySelector('.file-text');
    
    if (fileInput && fileText) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                fileText.textContent = e.target.files[0].name;
            } else {
                fileText.textContent = 'Choose receipt file';
            }
        });
    }
});
