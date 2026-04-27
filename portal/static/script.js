document.getElementById('reportForm').addEventListener('submit', function (e) {
    // We do NOT prevent default here, allowing the form to submit naturally to the server.

    const generateBtn = document.getElementById('generateBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('spinner');

    // Show loading state immediately
    generateBtn.disabled = true;
    btnText.textContent = 'Generating... (Please Wait)';
    spinner.classList.remove('hidden');

    // The browser will now navigate to /generate
});
