// Global elements and state
let term;
let fitAddon;
let socket = null;
let passcodeRequired = false;

// Theme configuration presets
const THEMES = {
    matrix: {
        theme: {
            background: '#000000',
            foreground: '#00ff00',
            cursor: '#00ff00',
            cursorAccent: '#000000',
            selectionBackground: 'rgba(0, 255, 0, 0.3)',
            black: '#000000',
            red: '#ff5555',
            green: '#00ff00',
            yellow: '#ffff55',
            blue: '#5555ff',
            magenta: '#ff55ff',
            cyan: '#55ffff',
            white: '#bbbbbb',
            brightBlack: '#555555',
            brightRed: '#ff5555',
            brightGreen: '#55ff55',
            brightYellow: '#ffff55',
            brightBlue: '#5555ff',
            brightMagenta: '#ff55ff',
            brightCyan: '#55ffff',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-matrix-glow)'
    },
    amber: {
        theme: {
            background: '#000000',
            foreground: '#ffb000',
            cursor: '#ffb000',
            cursorAccent: '#000000',
            selectionBackground: 'rgba(255, 176, 0, 0.3)',
            black: '#000000',
            red: '#ff5555',
            green: '#00ff00',
            yellow: '#ffff55',
            blue: '#5555ff',
            magenta: '#ff55ff',
            cyan: '#55ffff',
            white: '#bbbbbb',
            brightBlack: '#555555',
            brightRed: '#ff5555',
            brightGreen: '#55ff55',
            brightYellow: '#ffff55',
            brightBlue: '#5555ff',
            brightMagenta: '#ff55ff',
            brightCyan: '#55ffff',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-amber-glow)'
    },
    cyber: {
        theme: {
            background: '#0a0915',
            foreground: '#00f0ff',
            cursor: '#ff007f',
            cursorAccent: '#0a0915',
            selectionBackground: 'rgba(255, 0, 127, 0.3)',
            black: '#0a0915',
            red: '#ff0055',
            green: '#00ff66',
            yellow: '#ffcc00',
            blue: '#00aaff',
            magenta: '#ff00bb',
            cyan: '#00ffff',
            white: '#ffffff',
            brightBlack: '#555555',
            brightRed: '#ff0055',
            brightGreen: '#00ff66',
            brightYellow: '#ffcc00',
            brightBlue: '#00aaff',
            brightMagenta: '#ff00bb',
            brightCyan: '#00ffff',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-cyber-glow)'
    },
    dracula: {
        theme: {
            background: '#282a36',
            foreground: '#f8f8f2',
            cursor: '#f8f8f2',
            cursorAccent: '#282a36',
            selectionBackground: 'rgba(189, 147, 249, 0.3)',
            black: '#21222c',
            red: '#ff5555',
            green: '#50fa7b',
            yellow: '#f1fa8c',
            blue: '#bd93f9',
            magenta: '#ff79c6',
            cyan: '#8be9fd',
            white: '#f8f8f2',
            brightBlack: '#6272a4',
            brightRed: '#ff6e6e',
            brightGreen: '#69ff94',
            brightYellow: '#ffffa5',
            brightBlue: '#d6acff',
            brightMagenta: '#ff92df',
            brightCyan: '#a4ffff',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-dracula-glow)'
    },
    classic: {
        theme: {
            background: '#111116',
            foreground: '#e5e7eb',
            cursor: '#ffffff',
            cursorAccent: '#111116',
            selectionBackground: 'rgba(255, 255, 255, 0.15)',
            black: '#000000',
            red: '#ef4444',
            green: '#10b981',
            yellow: '#f59e0b',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#e5e7eb',
            brightBlack: '#4b5563',
            brightRed: '#ef4444',
            brightGreen: '#10b981',
            brightYellow: '#f59e0b',
            brightBlue: '#3b82f6',
            brightMagenta: '#a855f7',
            brightCyan: '#06b6d4',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-classic-glow)'
    },
    monochrome: {
        theme: {
            background: '#000000',
            foreground: '#ffffff',
            cursor: '#ffffff',
            cursorAccent: '#000000',
            selectionBackground: 'rgba(255, 255, 255, 0.3)',
            black: '#000000',
            red: '#ffffff',
            green: '#ffffff',
            yellow: '#ffffff',
            blue: '#ffffff',
            magenta: '#ffffff',
            cyan: '#ffffff',
            white: '#ffffff',
            brightBlack: '#888888',
            brightRed: '#ffffff',
            brightGreen: '#ffffff',
            brightYellow: '#ffffff',
            brightBlue: '#ffffff',
            brightMagenta: '#ffffff',
            brightCyan: '#ffffff',
            brightWhite: '#ffffff'
        },
        glow: 'var(--term-classic-glow)'
    }
};

// Initialize Frontend Application
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    // 1. Fetch Backend Config (does it require passcode?)
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        passcodeRequired = data.passcode_required;
        
        const passcodeCard = document.getElementById('passcode-card');
        if (passcodeRequired) {
            passcodeCard.classList.remove('hidden');
            // Auto fill passcode if saved
            const savedPass = localStorage.getItem('mybbs_passcode');
            if (savedPass) {
                document.getElementById('txt-passcode').value = savedPass;
            }
        } else {
            passcodeCard.classList.add('hidden');
        }
    } catch (e) {
        console.error("Failed to load configuration from backend", e);
    }

    // 2. Setup passcode visibility toggle
    document.getElementById('btn-toggle-passcode-view').addEventListener('click', () => {
        const input = document.getElementById('txt-passcode');
        const icon = document.querySelector('#btn-toggle-passcode-view i');
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.replace('fa-eye-slash', 'fa-eye');
        }
    });

    // 3. Initialize xterm.js
    term = new Terminal({
        cols: 80,
        rows: 24,
        cursorBlink: true,
        fontFamily: "'Courier New', 'MingLiU', 'PMingLiU', 'Microsoft JhengHei', monospace",
        fontSize: parseInt(document.getElementById('rng-font-size').value),
        letterSpacing: 0,
        lineHeight: 1.25,
        convertEol: true,
        scrollback: 1000
    });

    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    
    // Optional web-links support
    const webLinksAddon = new window.WebLinksAddon.WebLinksAddon();
    term.loadAddon(webLinksAddon);

    const termContainer = document.getElementById('terminal');
    term.open(termContainer);
    fitAddon.fit();

    // Setup initial theme
    updateTheme(document.getElementById('sel-theme').value);

    // 4. Handle Window Resize
    window.addEventListener('resize', () => {
        fitAddon.fit();
    });

    // 5. Connect / Disconnect Action Button
    const btnToggleConn = document.getElementById('btn-toggle-conn');
    btnToggleConn.addEventListener('click', () => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            disconnectPTT();
        } else {
            connectPTT();
        }
    });

    // 6. Font Size Slider Adjustments
    const rngFontSize = document.getElementById('rng-font-size');
    const lblFontSize = document.getElementById('lbl-font-size');
    rngFontSize.addEventListener('input', (e) => {
        const val = e.target.value;
        lblFontSize.textContent = `${val}px`;
        term.options.fontSize = parseInt(val);
        fitAddon.fit();
    });

    // 7. Theme Selection Change
    const selTheme = document.getElementById('sel-theme');
    selTheme.addEventListener('change', (e) => {
        updateTheme(e.target.value);
    });

    // 8. Virtual BBS Keypad Actions
    document.querySelectorAll('.key-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.key;
            sendKey(key);
        });
    });

    // 9. Fullscreen Mode Toggle
    const btnFullscreen = document.getElementById('btn-fullscreen');
    btnFullscreen.addEventListener('click', () => {
        document.body.classList.toggle('fullscreen-mode');
        const icon = btnFullscreen.querySelector('i');
        if (document.body.classList.contains('fullscreen-mode')) {
            icon.classList.replace('fa-expand', 'fa-compress');
        } else {
            icon.classList.replace('fa-compress', 'fa-expand');
        }
        setTimeout(() => {
            fitAddon.fit();
        }, 100);
    });

    // 10. Paste Helper Modal Controls
    const pasteModal = document.getElementById('paste-overlay'); // wait, overlay is named paste-modal in html
    const btnOpenPaste = document.getElementById('btn-open-paste');
    const btnClosePaste = document.getElementById('btn-close-paste');
    const btnCancelPaste = document.getElementById('btn-cancel-paste');
    const btnSubmitPaste = document.getElementById('btn-submit-paste');
    const modalEl = document.getElementById('paste-modal');

    btnOpenPaste.addEventListener('click', () => {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            alert("請先建立 PTT 連線！");
            return;
        }
        document.getElementById('paste-text-area').value = '';
        modalEl.classList.remove('hidden');
        document.getElementById('paste-progress-container').classList.add('hidden');
        document.getElementById('paste-progress').style.width = '0%';
    });

    const closeModal = () => {
        modalEl.classList.add('hidden');
    };
    btnClosePaste.addEventListener('click', closeModal);
    btnCancelPaste.addEventListener('click', closeModal);

    btnSubmitPaste.addEventListener('click', handleSafePaste);

    // Initial greeting in terminal
    term.write("Welcome to myBBS PTT Jumpboard!\r\n");
    term.write("-------------------------------------\r\n");
    term.write("請使用左側控制台的 [連線到 PTT] 按鈕開始使用。\r\n");
}

// Update terminal theme options
function updateTheme(themeName) {
    const config = THEMES[themeName];
    if (!config) return;
    
    // Set xterm.js theme options
    term.options.theme = config.theme;
    
    // Set CSS active glow variables for the container box-shadow
    document.documentElement.style.setProperty('--active-glow', config.glow);
}

// Websocket Connection
function connectPTT() {
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const btnToggleConn = document.getElementById('btn-toggle-conn');

    // Get passcode if required
    let passcode = "";
    if (passcodeRequired) {
        passcode = document.getElementById('txt-passcode').value.trim();
        if (passcode && document.getElementById('chk-save-passcode').checked) {
            localStorage.setItem('mybbs_passcode', passcode);
        } else if (!passcode) {
            alert("請輸入訪問密碼！");
            return;
        }
    }

    // Set UI to connecting
    statusIndicator.className = "status-dot connecting";
    statusText.textContent = "連線中...";
    btnToggleConn.disabled = true;

    // Determine WS protocol and URL
    const loc = window.location;
    const wsProto = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${loc.host}/ws?passcode=${encodeURIComponent(passcode)}`;

    term.clear();
    term.focus();

    socket = new WebSocket(wsUrl);

    // Hook term data to WS sending
    term.onData(data => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(data);
        }
    });

    socket.onopen = () => {
        statusIndicator.className = "status-dot connected";
        statusText.textContent = "已連線 PTT";
        btnToggleConn.disabled = false;
        btnToggleConn.className = "btn btn-disconnect";
        btnToggleConn.innerHTML = '<i class="fa-solid fa-stop"></i> <span>中斷連線</span>';
        fitAddon.fit();
    };

    socket.onmessage = (event) => {
        term.write(event.data);
    };

    socket.onclose = (event) => {
        console.log("WebSocket connection closed", event);
        disconnectUI();
        if (event.code === 1008) {
            term.write("\r\n\x1b[1;31m[System] 連線拒絕：安全存取密碼錯誤。\x1b[0m\r\n");
        } else {
            term.write("\r\n\x1b[1;33m[System] 與代理伺服器的連線已關閉。\x1b[0m\r\n");
        }
    };

    socket.onerror = (error) => {
        console.error("WebSocket connection error", error);
        disconnectUI();
        term.write("\r\n\x1b[1;31m[System] 連線發生錯誤。\x1b[0m\r\n");
    };
}

function disconnectPTT() {
    if (socket) {
        socket.close();
    }
    disconnectUI();
}

function disconnectUI() {
    socket = null;
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const btnToggleConn = document.getElementById('btn-toggle-conn');

    statusIndicator.className = "status-dot disconnected";
    statusText.textContent = "未連線";
    btnToggleConn.disabled = false;
    btnToggleConn.className = "btn btn-connect";
    btnToggleConn.innerHTML = '<i class="fa-solid fa-play"></i> <span>連線到 PTT</span>';
}

// Send keyboard mappings or raw codes
function sendKey(key) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    
    let keySeq = "";
    switch(key) {
        case "ArrowUp":
            keySeq = "\x1b[A";
            break;
        case "ArrowDown":
            keySeq = "\x1b[B";
            break;
        case "ArrowRight":
            keySeq = "\x1b[C";
            break;
        case "ArrowLeft":
            keySeq = "\x1b[D";
            break;
        case "Enter":
            keySeq = "\r";
            break;
        case "Escape":
            keySeq = "\x1b";
            break;
        default:
            return;
    }
    socket.send(keySeq);
    term.focus();
}

// Paste helper logic: chunk writing to avoid spam throttle
function handleSafePaste() {
    const text = document.getElementById('paste-text-area').value;
    if (!text) {
        alert("請貼上文字內容！");
        return;
    }

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert("請確認連線狀態！");
        return;
    }

    const btnSubmit = document.getElementById('btn-submit-paste');
    const btnCancel = document.getElementById('btn-cancel-paste');
    const progressContainer = document.getElementById('paste-progress-container');
    const progressBar = document.getElementById('paste-progress');
    const progressText = document.getElementById('paste-progress-text');

    // Disable action buttons inside modal
    btnSubmit.disabled = true;
    btnCancel.disabled = true;
    progressContainer.classList.remove('hidden');

    // BBS typically uses CRLF for newlines, so map newlines to carriage return \r
    const cleanText = text.replace(/\r?\n/g, '\r');
    
    let offset = 0;
    const chunkSize = 20; // 20 chars per tick
    const delay = 50; // 50ms interval

    progressText.textContent = "正在傳送中，請勿關閉視窗...";

    const timer = setInterval(() => {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            clearInterval(timer);
            alert("傳送中途斷連！");
            btnSubmit.disabled = false;
            btnCancel.disabled = false;
            progressContainer.classList.add('hidden');
            return;
        }

        if (offset >= cleanText.length) {
            clearInterval(timer);
            // Completed!
            progressBar.style.width = '100%';
            progressText.textContent = "傳送完畢！";
            setTimeout(() => {
                btnSubmit.disabled = false;
                btnCancel.disabled = false;
                document.getElementById('paste-modal').classList.add('hidden');
            }, 500);
            return;
        }

        const chunk = cleanText.substring(offset, offset + chunkSize);
        socket.send(chunk);
        offset += chunkSize;

        // Update progress bar
        const pct = Math.min(100, Math.floor((offset / cleanText.length) * 100));
        progressBar.style.width = `${pct}%`;
    }, delay);
}
