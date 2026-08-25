// website/script.js
document.addEventListener('DOMContentLoaded', () => {
    // 1. Interactive Command Showcase Click Handlers
    const pills = document.querySelectorAll('.cmd-pill');
    const previewCmd = document.getElementById('preview-cmd');
    const previewLane = document.getElementById('preview-lane');
    const previewAction = document.getElementById('preview-action');

    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            const cmd = pill.getAttribute('data-cmd');
            const lane = pill.getAttribute('data-lane');
            const action = pill.getAttribute('data-action');

            if (previewCmd) previewCmd.textContent = `"${cmd}"`;
            if (previewLane) previewLane.textContent = lane;
            if (previewAction) previewAction.textContent = action;
        });
    });

    // 2. Animated Typing Effect in Hero
    const phrases = [
        '"Alexa, open Chrome"',
        '"Alexa, launch WhatsApp"',
        '"Alexa, open browser"',
        '"Alexa, bring up code editor"'
    ];
    let phraseIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    const typingElement = document.getElementById('typing-text');

    function typeLoop() {
        if (!typingElement) return;
        const currentPhrase = phrases[phraseIdx];
        
        if (isDeleting) {
            typingElement.textContent = currentPhrase.substring(0, charIdx - 1);
            charIdx--;
        } else {
            typingElement.textContent = currentPhrase.substring(0, charIdx + 1);
            charIdx++;
        }

        let speed = isDeleting ? 40 : 80;

        if (!isDeleting && charIdx === currentPhrase.length) {
            speed = 2000; // Pause at end of sentence
            isDeleting = true;
        } else if (isDeleting && charIdx === 0) {
            isDeleting = false;
            phraseIdx = (phraseIdx + 1) % phrases.length;
            speed = 500;
        }

        setTimeout(typeLoop, speed);
    }

    typeLoop();
});
