document.addEventListener('DOMContentLoaded', () => { 
    // Usamos la URL del backend local para esta integración
    const API_BASE_URL = '/api';  

    const chatListElement = document.getElementById('chat-list');
    const chatViewElement = document.getElementById('chat-view');
    const welcomeViewElement = document.getElementById('welcome-view');   
    const sidebarElement = document.getElementById('sidebar');
    const backBtn = document.getElementById('back-btn');
    const botSelector = document.getElementById('bot-selector-main');     
    const attachBtn = document.getElementById('attach-btn');
    const mediaInput = document.getElementById('media-upload-input');

    let currentPhone = null;
    let messagesInterval = null;
    let chatsInterval = null;
    let currentBotId = 'default';

    // --- Gestión de Sesión ---
    async function checkSession() {
        const token = localStorage.getItem("session_token");
        if (!token) {
            window.location.href = "login.html";
            return false;
        }
        try {
            const res = await fetch(`${API_BASE_URL}/chats`, {
                headers: { "Authorization": token }
            });
            if (res.status === 401) {
                localStorage.removeItem("session_token");
                window.location.href = "login.html";
                return false;
            }
            return true;
        } catch (e) {
            console.error("Error validando sesión", e);
            return true; // Permitimos continuar si es un error de red
        }
    }

    async function authenticatedFetch(url, options = {}) {
        const token = localStorage.getItem("session_token");
        const headers = { ...options.headers, "Authorization": token };
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            localStorage.removeItem("session_token");
            window.location.href = "login.html";
        }
        return response;
    }

    // --- Funciones de UI y Responsividad --- 
    function showChatView() {
        welcomeViewElement.classList.add('hidden');
        chatViewElement.classList.remove('hidden');
        if (window.innerWidth <= 768) {
            sidebarElement.classList.add('hidden-mobile');
            backBtn.classList.remove('hidden');
        } else {
            backBtn.classList.add('hidden');
        }
    }

    function showSidebar() {
        if (window.innerWidth <= 768) {
            sidebarElement.classList.remove('hidden-mobile');
            chatViewElement.classList.add('hidden');
        } else {
            welcomeViewElement.classList.remove('hidden');
            chatViewElement.classList.add('hidden'); 
        }
        backBtn.classList.add('hidden');
        currentPhone = null;
        if(messagesInterval) clearInterval(messagesInterval);
        document.querySelectorAll('#chat-list li').forEach(el => el.classList.remove('selected'));
    }

    backBtn.addEventListener('click', showSidebar);

    botSelector.addEventListener('change', (e) => {
        currentBotId = e.target.value;
        showSidebar();
        fetchConversations();
    });

    // --- Funciones API ---
    async function fetchConversations() { 
        try {
            const res = await authenticatedFetch(`${API_BASE_URL}/chats`);
            if (!res.ok) throw new Error("API error");
            const conversations = await res.json();
            renderChatList(conversations);
        } catch (e) {
            console.error('Error fetching conversations:', e);
            if (!chatListElement.innerHTML.includes('li')) {
                chatListElement.innerHTML = '<li style="padding:15px; color:red;">Error de conexiÃ³n. Reintentando...</li>';
            }
        }
    }

    function renderChatList(conversations) {
        if (!conversations || conversations.length === 0) {
            chatListElement.innerHTML = '<li style="padding:15px;">No hay conversaciones.</li>';
            return; 
        }

        const currentElements = Array.from(chatListElement.children);
        const incomingPhones = conversations.map(c => c.phone_number);

        conversations.forEach(chat => {
            let li = chatListElement.querySelector(`li[data-phone="${chat.phone_number}"]`);
            const isActive = (String(chat.is_human_intervening) === 'true');
            const name = chat.name || 'Desconocido';

            if (!li) {
                li = document.createElement('li');
                li.dataset.phone = chat.phone_number;
                chatListElement.appendChild(li);
            }

            li.dataset.name = name;
            li.dataset.isHuman = chat.is_human_intervening;

            const contentHtml = `
                <div class="chat-item-name">
                    <span>${name}</span>
                    <span>${isActive ? 'ðŸ‘¤' : 'ðŸ¤–'}</span>
                </div>
                <div class="chat-item-phone">${chat.phone_number}</div>
            `;

            if (li.innerHTML !== contentHtml) {
                li.innerHTML = contentHtml;
            }

            if (currentPhone === chat.phone_number) {
                li.classList.add('selected');
                updateInterventionButton(chat.is_human_intervening);
            } else {
                li.classList.remove('selected');
            }
        });

        currentElements.forEach(el => {
            if (el.dataset.phone && !incomingPhones.includes(el.dataset.phone)) { 
                el.remove();
            }
        });
    }

    function updateInterventionButton(isHuman) {
        const btn = document.getElementById('human-toggle');
        if (btn) {
            const active = (String(isHuman) === 'true');
            btn.className = active ? 'active' : '';
            btn.textContent = active ? 'ðŸ‘¤ Modo Humano (ON)' : 'ðŸ¤– Modo Bot (ON)';

            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', () => toggleHuman(currentPhone, active));
        }
    }

    async function loadChatDetail(phone, name, isHuman) {
        currentPhone = phone;

        document.querySelectorAll('#chat-list li').forEach(li => {
            li.classList.toggle('selected', li.dataset.phone === phone);
        });

        document.getElementById('chat-header-name').textContent = name;
        document.getElementById('chat-header-phone').textContent = phone;

        showChatView();
        updateInterventionButton(isHuman);

        document.getElementById('messages-container').innerHTML = '<div style="text-align:center; padding: 20px;">Cargando mensajes...</div>';

        const sendBtn = document.getElementById('send-message-btn');
        const newSendBtn = sendBtn.cloneNode(true);
        sendBtn.parentNode.replaceChild(newSendBtn, sendBtn);
        newSendBtn.addEventListener('click', () => sendMessage(phone));

        const inputTxt = document.getElementById('message-input-text');
        const newInputTxt = inputTxt.cloneNode(true);
        inputTxt.parentNode.replaceChild(newInputTxt, inputTxt);
        newInputTxt.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage(phone);
        });

        const deleteBtn = document.getElementById('delete-chat-btn');
        if (deleteBtn) { 
            const newDeleteBtn = deleteBtn.cloneNode(true);
            deleteBtn.parentNode.replaceChild(newDeleteBtn, deleteBtn);
            newDeleteBtn.addEventListener('click', () => deleteConversation(phone));
        }

        await fetchMessages(phone);

        if (messagesInterval) clearInterval(messagesInterval);
        messagesInterval = setInterval(() => {
            if (currentPhone === phone) fetchMessages(phone, false);
        }, 3000);
    }

    async function deleteConversation(phone) {
        if (!confirm('Â¿EstÃ¡s seguro de que deseas borrar toda la conversaciÃ³n con ' + phone + '? Esta acciÃ³n no se puede deshacer.')) return;

        try {
            const res = await authenticatedFetch(`${API_BASE_URL}/chats/${phone}/delete`, {
                method: 'POST'
            });

            if (res.ok) {
                if (currentPhone === phone) {
                    showSidebar();
                }
                fetchConversations();
            } else {
                const errorText = await res.text();
                alert(`Error ${res.status} al borrar la conversaciÃ³n.
Detalle: ${errorText}`);
            }
        } catch (error) {
            console.error('Error de red:', error);
            alert(`Error de conexiÃ³n:
${error.message}`);
        }
    }

    async function fetchMessages(phone, showLoading = true) {
        try {
            const res = await authenticatedFetch(`${API_BASE_URL}/chats/${phone}/messages`);
            const messages = await res.json();
            if (currentPhone === phone) {
                renderMessages(messages);
            }
        } catch (e) {
            console.error('Error fetching messages:', e);
            if (showLoading) {
                document.getElementById('messages-container').innerHTML = '<div style="color:red; text-align:center; padding: 20px;">Error al cargar.</div>';   
            }
        }
    }

    function renderMessages(messages) { 
        const container = document.getElementById('messages-container');
        if (!container) return;

        const isScrolledToBottom = container.scrollHeight - container.clientHeight <= container.scrollTop + 50;

        container.innerHTML = messages.map(msg => {
            const isClient = msg.sender === 'client';
            const typeClass = isClient ? 'received' : 'sent';

            let senderLabel = '';
            if (msg.sender === 'bot') senderLabel = '<span class="msg-sender-label" style="color:#008069;">ðŸ¤– Bot</span>';
            if (msg.sender === 'human') senderLabel = '<span class="msg-sender-label" style="color:#53bdeb;">ðŸ‘¤ TÃº</span>';

            const d = new Date(msg.timestamp);
            const timeStr = isNaN(d) ? '' : `<span class="msg-meta">${d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>`;

            return `<div class="message ${typeClass}">${senderLabel}${msg.content}${timeStr}</div>`;
        }).join('');

        if (isScrolledToBottom || !container.dataset.loaded) {
            container.scrollTop = container.scrollHeight;
            container.dataset.loaded = 'true';
        }
    }

    async function sendMessage(phone) {
        const input = document.getElementById('message-input-text');
        const text = input.value.trim();
        if (text === '') return;

        input.value = '';
        input.focus();

        const container = document.getElementById('messages-container');
        if (container) {
            const optimisticMsg = `<div class="message sent" style="opacity: 0.6;"><span class="msg-sender-label" style="color:#53bdeb;">ðŸ‘¤ TÃº</span>${text}<span class="msg-meta">Enviando...</span></div>`;
            container.insertAdjacentHTML('beforeend', optimisticMsg); 
            container.scrollTop = container.scrollHeight;
        }

        try {
            await authenticatedFetch(`${API_BASE_URL}/chats/${phone}/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            await fetchMessages(phone, false);
        } catch (e) {
            console.error('Error:', e);
            alert("Error al enviar mensaje.");
            await fetchMessages(phone, false);
        }
    }

    if (attachBtn && mediaInput) {
        attachBtn.addEventListener('click', () => {
            if (!currentPhone) return;
            mediaInput.click();
        }); 

        mediaInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file || !currentPhone) return;

            const captionInput = document.getElementById('message-input-text');
            const caption = captionInput.value.trim();
            captionInput.value = '';

            const container = document.getElementById('messages-container');
            if (container) {
                const optimisticMsg = `<div class="message sent" style="opacity: 0.6;"><span class="msg-sender-label" style="color:#53bdeb;">ðŸ‘¤ TÃº</span>ðŸ“Ž Enviando archivo: ${file.name}...<span class="msg-meta">Subiendo...</span></div>`;
                container.insertAdjacentHTML('beforeend', optimisticMsg);
                container.scrollTop = container.scrollHeight;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('phone_number', currentPhone);
            if (caption) {
                formData.append('caption', caption);
            }

            try {
                const res = await authenticatedFetch(`${API_BASE_URL}/media`, {
                    method: 'POST',
                    body: formData
                });

                if (!res.ok) {
                    const errText = await res.text();
                    alert(`Error enviando archivo: ${errText}`);
                }
                await fetchMessages(currentPhone, false);
            } catch (error) {
                console.error('Error enviando archivo:', error);
                alert(`Error de conexiÃ³n al enviar el archivo.`);
            } finally {
                mediaInput.value = '';
            }
        }); 
    }

    async function toggleHuman(phone, currentlyActive) {
        const newStatus = !currentlyActive;
        updateInterventionButton(newStatus);

        try {
            await authenticatedFetch(`${API_BASE_URL}/chats/${phone}/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_human_intervening: newStatus })
            });
            fetchConversations();
        } catch (e) {
            console.error('Error:', e);
            alert("Error de red.");
            updateInterventionButton(currentlyActive);
        }
    }

    chatListElement.addEventListener('click', (event) => {
        const li = event.target.closest('li');
        if (li && li.dataset.phone) { 
            loadChatDetail(li.dataset.phone, li.dataset.name, li.dataset.isHuman);
        }
    });

    checkSession().then(isValid => {
        if (isValid) {
            fetchConversations();
            chatsInterval = setInterval(fetchConversations, 5000);
        }
    });
});
