document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('shmasChatToggle');
  const chatWindow = document.getElementById('shmasChatWindow');
  const closeBtn = document.getElementById('shmasChatClose');
  const messagesEl = document.getElementById('shmasChatMessages');
  const input = document.getElementById('shmasChatInput');
  const sendBtn = document.getElementById('shmasChatSend');
  const micBtn = document.getElementById('shmasChatMic');

  if (!toggleBtn || !chatWindow) return; // widget not present on this page

  toggleBtn.addEventListener('click', () => {
    chatWindow.classList.toggle('d-none');
    if (!chatWindow.classList.contains('d-none')) {
      input.focus();
    }
  });
  closeBtn.addEventListener('click', () => chatWindow.classList.add('d-none'));

  function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = 'shmas-msg ' + (sender === 'user' ? 'shmas-msg-user' : 'shmas-msg-bot');
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    input.value = '';
    sendBtn.disabled = true;
    const typingEl = addMessage('Typing...', 'bot');
    typingEl.classList.add('shmas-msg-typing');

    try {
      const resp = await fetch('/health/chatbot/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ message: text }),
      });
      const data = await resp.json();
      typingEl.remove();
      if (data && data.reply) {
        addMessage(data.reply, 'bot');
      } else {
        addMessage("Sorry, I couldn't process that. Please try again.", 'bot');
      }
    } catch (e) {
      typingEl.remove();
      addMessage('Connection issue -- please try again.', 'bot');
    } finally {
      sendBtn.disabled = false;
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  // Voice input (Web Speech API) is an ADDITION -- typing always still works,
  // even in browsers that don't support speech recognition.
  // continuous + interimResults so the mic keeps listening through natural
  // pauses instead of cutting off mid-sentence, and the input box updates
  // live as the person speaks. Tap the mic again to stop.
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition && micBtn) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = true;

    let listening = false;
    let finalTranscript = '';

    micBtn.addEventListener('click', () => {
      if (listening) {
        recognition.stop(); // tap again to finish speaking
        return;
      }
      finalTranscript = input.value ? input.value.trim() + ' ' : '';
      try {
        recognition.start();
        listening = true;
        micBtn.classList.add('listening');
      } catch (e) {
        // recognition already active or blocked; ignore
      }
    });
    recognition.addEventListener('result', (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const transcript = e.results[i][0].transcript;
        if (e.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interim += transcript;
        }
      }
      input.value = (finalTranscript + interim).trim();
    });
    recognition.addEventListener('end', () => {
      listening = false;
      micBtn.classList.remove('listening');
    });
    recognition.addEventListener('error', () => {
      listening = false;
      micBtn.classList.remove('listening');
    });
  } else if (micBtn) {
    micBtn.style.display = 'none'; // browser doesn't support voice input; typing still works fine
  }
});
