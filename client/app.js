// SEECHAT CLIENT APPLICATION LOGIC
const isFileProtocol = window.location.protocol === 'file:';

let socket;
if (isFileProtocol) {
  socket = io('http://127.0.0.1:8080');
} else {
  socket = io();
}

// State Management - Session Persistence & JWT Security
let myUsername = localStorage.getItem('seechat_active_username') || '';
let savedPassword = localStorage.getItem('seechat_active_password') || '';
let jwtToken = localStorage.getItem('seechat_jwt_token') || '';
let myRole = 'user';
let currentTarget = null;
let onlineUsers = [];
let broadcastGroups = [];
let pinnedUsers = JSON.parse(localStorage.getItem('seechat_pinned_users') || '[]');
let mutedUsers = JSON.parse(localStorage.getItem('seechat_muted_users') || '[]');
let activeTab = 'users';
let chatHistories = {};
let unreadCounts = {};
let myMoodStatus = 'Available';
let typingTimer = null;
let currentReqStatus = 'none'; // 'accepted', 'pending_out', 'pending_in', 'none'
let selectedRightClickUser = null;
let selectedRightClickGroup = null;

let originalDocumentTitle = document.title;
let titleBlinkInterval = null;

// DOM Elements
const loginModalOverlay = document.getElementById('login-modal-overlay');
const loginForm = document.getElementById('login-form');
const loginUsernameInput = document.getElementById('login-username');
const loginPasswordInput = document.getElementById('login-password');
const btnToggleEye = document.getElementById('btn-toggle-eye');
const loginErrorText = document.getElementById('login-error');
const btnLogout = document.getElementById('btn-logout');
const btnLoginSubmit = document.getElementById('btn-login-submit');

const appContainer = document.getElementById('app-container');
const myAvatar = document.getElementById('my-avatar');
const myUsernameEl = document.getElementById('my-username');
const myMoodSelect = document.getElementById('my-mood-select');
const typingIndicator = document.getElementById('typing-indicator');
const typingUsername = document.getElementById('typing-username');


const userSearchInput = document.getElementById('user-search-input');
const usersListEl = document.getElementById('users-list');
const groupsListEl = document.getElementById('groups-list');
const onlineCountEl = document.getElementById('online-count');
const adminTabBtn = document.getElementById('admin-tab-btn');
const fullAdminPanel = document.getElementById('full-admin-panel');
const btnCloseAdminPanel = document.getElementById('btn-close-admin-panel');

const chatHeader = document.querySelector('.chat-header');
const targetAvatar = document.getElementById('target-avatar');
const targetTitle = document.getElementById('target-title');
const chatHeaderActions = document.getElementById('chat-header-actions');
const groupHeaderActions = document.getElementById('group-header-actions');

const btnPingDesk = document.getElementById('btn-ping-desk');
const btnClearChat = document.getElementById('btn-clear-chat');
const btnRenameGroup = document.getElementById('btn-rename-group');
const btnDeleteGroup = document.getElementById('btn-delete-group');

const messagesContainer = document.getElementById('messages-container');
const emptyChatPlaceholder = document.getElementById('empty-chat-placeholder');
const messagesList = document.getElementById('messages-list');
const chatRequestContainer = document.getElementById('chat-request-container');
const requestCardTitle = document.getElementById('request-card-title');
const requestCardSubtext = document.getElementById('request-card-subtext');
const requestActionsArea = document.getElementById('request-actions-area');

const chatInputBar = document.getElementById('chat-input-bar');
const messageInput = document.getElementById('message-input');
const btnSend = document.getElementById('btn-send');

const btnTogglePresets = document.getElementById('btn-toggle-presets');
const presetsBar = document.getElementById('presets-bar');
const btnToggleEmoji = document.getElementById('btn-toggle-emoji');
const emojiPicker = document.getElementById('emoji-picker');

// CONTEXT MENU ELEMENTS FOR TEAM MEMBERS
const contextMenu = document.getElementById('context-menu');
const ctxMuteUser = document.getElementById('ctx-mute-user');
const ctxPinUser = document.getElementById('ctx-pin-user');
const ctxAddToGroup = document.getElementById('ctx-add-to-group');
const ctxClearUserChat = document.getElementById('ctx-clear-user-chat');

// CONTEXT MENU ELEMENTS FOR GROUPS
const groupContextMenu = document.getElementById('group-context-menu');
const ctxRenameGroup = document.getElementById('ctx-rename-group');
const ctxEditGroupMembers = document.getElementById('ctx-edit-group-members');
const ctxDeleteGroup = document.getElementById('ctx-delete-group');

// CREATE / ADD TO GROUP MODAL ELEMENTS
const createGroupModal = document.getElementById('create-group-modal');
const groupModalTitle = document.getElementById('group-modal-title');
const btnOpenCreateGroup = document.getElementById('btn-open-create-group');
const btnCancelGroupModal = document.getElementById('btn-cancel-group-modal');
const btnSaveGroup = document.getElementById('btn-save-group');
const groupNameInput = document.getElementById('group-name-input');
const groupMemberSearchInput = document.getElementById('group-member-search-input');
const groupMembersChecklist = document.getElementById('group-members-checklist');
const selectedMembersCount = document.getElementById('selected-members-count');
const selectedMembersChips = document.getElementById('selected-members-chips');
let selectedGroupMemberSet = new Set();

// REPLY PREVIEW ELEMENTS
const replyPreviewBar = document.getElementById('reply-preview-bar');
const replyTargetSender = document.getElementById('reply-target-sender');
const replyTargetText = document.getElementById('reply-target-text');
const btnCancelReply = document.getElementById('btn-cancel-reply');
let pendingReplyMessage = null;

let liveAnimatedMsgIds = new Set();
let pendingDeliveryAcks = new Set();

// EDIT & DELETE PREVIEW & MODAL ELEMENTS
const editPreviewBar = document.getElementById('edit-preview-bar');
const editTargetText = document.getElementById('edit-target-text');
const btnCancelEdit = document.getElementById('btn-cancel-edit');
let pendingEditMessage = null;

const deleteConfirmModal = document.getElementById('delete-confirm-modal');
const btnCancelDelete = document.getElementById('btn-cancel-delete');
const btnConfirmDelete = document.getElementById('btn-confirm-delete');
let pendingDeleteMessageId = null;
let userActivityTimestamps = {};

// CUSTOM CLEAR CHAT MODAL ELEMENTS
const clearChatModal = document.getElementById('clear-chat-modal');
const btnCancelClearChat = document.getElementById('btn-cancel-clear-chat');
const btnConfirmClearChat = document.getElementById('btn-confirm-clear-chat');
let pendingClearTarget = null;

// ADMIN PANEL DOM ELEMENTS
const adminNoticeInput = document.getElementById('admin-notice-input');
const btnSendStudioNotice = document.getElementById('btn-send-studio-notice');
const adminAddUsername = document.getElementById('admin-add-username');
const adminAddRole = document.getElementById('admin-add-role');
const btnAdminAddUser = document.getElementById('btn-admin-add-user');
const adminUsersTableBody = document.getElementById('admin-users-table-body');

// SERVER HEALTH DOM ELEMENTS
const shPython = document.getElementById('sh-python');
const shSocket = document.getElementById('sh-socket');
const shDb = document.getElementById('sh-db');
const shCsv = document.getElementById('sh-csv');
const shConns = document.getElementById('sh-conns');
const shUptime = document.getElementById('sh-uptime');

let lastPopupSender = 'Demo_User';
let lastReqSender = null;
let editingGroupOriginalName = null;

// SLEEK NON-BLOCKING TOAST NOTIFICATION UTILITY
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// EYE ICON SHOW/HIDE PASSWORD TOGGLE
if (btnToggleEye && loginPasswordInput) {
  btnToggleEye.addEventListener('click', () => {
    const isPassword = loginPasswordInput.getAttribute('type') === 'password';
    loginPasswordInput.setAttribute('type', isPassword ? 'text' : 'password');
    btnToggleEye.textContent = isPassword ? '🙈' : '👁️';
  });
}

// --- 1. MANDATORY LOGIN CHECK WITH JWT AUTHENTICATION ---
function checkAuthSession() {
  const activeJwtToken = localStorage.getItem('seechat_jwt_token');
  if (activeJwtToken) {
    socket.emit('user_login', { token: activeJwtToken });
  } else if (myUsername && myUsername !== 'undefined') {
    socket.emit('user_login', { username: myUsername, password: savedPassword || 'nopassword', status: 'online' });
  } else {
    loginModalOverlay.classList.remove('hidden');
    appContainer.classList.add('hidden');
  }
}

function submitLoginForm() {
  const uname = loginUsernameInput.value.trim();
  const pwd = loginPasswordInput.value.trim();
  if (!uname) return;

  loginErrorText.classList.add('hidden');
  socket.emit('user_login', { username: uname, password: pwd || 'nopassword', status: 'online' });
}

if (loginForm) {
  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    submitLoginForm();
  });
}

if (btnLoginSubmit) {
  btnLoginSubmit.addEventListener('click', (e) => {
    e.preventDefault();
    submitLoginForm();
  });
}

socket.on('login_success', ({ username, role, token, unread_counts, mood_status }) => {
  myUsername = username;
  myRole = role || 'user';
  if (unread_counts) unreadCounts = unread_counts;
  if (mood_status) {
    myMoodStatus = mood_status;
    if (myMoodSelect) myMoodSelect.value = mood_status;
  }
  if (token) {
    localStorage.setItem('seechat_jwt_token', token);
  }
  localStorage.setItem('seechat_active_username', myUsername);

  myUsernameEl.textContent = myUsername;
  myAvatar.textContent = myUsername.charAt(0).toUpperCase();

  loginModalOverlay.classList.add('hidden');
  appContainer.classList.remove('hidden');

  if (myRole === 'admin') {
    if (adminTabBtn) adminTabBtn.classList.remove('hidden');
  } else {
    if (adminTabBtn) adminTabBtn.classList.add('hidden');
  }

  autoRequestNotificationPermission();
});

if (myMoodSelect) {
  myMoodSelect.addEventListener('change', () => {
    const selectedMood = myMoodSelect.value;
    myMoodStatus = selectedMood;
    socket.emit('update_mood_status', { mood_status: selectedMood });
  });
}


socket.on('login_failed', ({ error }) => {
  localStorage.removeItem('seechat_jwt_token');
  loginErrorText.textContent = error || 'Authentication failed.';
  loginErrorText.style.color = '#f38ba8';
  loginErrorText.classList.remove('hidden');
  loginModalOverlay.classList.remove('hidden');
  appContainer.classList.add('hidden');
});

if (btnLogout) {
  btnLogout.addEventListener('click', () => {
    localStorage.removeItem('seechat_active_username');
    localStorage.removeItem('seechat_active_password');
    localStorage.removeItem('seechat_jwt_token');
    myUsername = '';
    savedPassword = '';
    appContainer.classList.add('hidden');
    loginModalOverlay.classList.remove('hidden');
    loginUsernameInput.value = '';
    if (loginPasswordInput) loginPasswordInput.value = '';
    loginErrorText.classList.add('hidden');
  });
}

// --- 2. BROWSER NOTIFICATION PERMISSION PROMPT ---
function autoRequestNotificationPermission() {
  if ('Notification' in window) {
    if (Notification.permission === 'default') {
      showToast('🔔 Notification Alert: Please click "Allow" in your browser prompt for floating alerts!', 'info');
      try {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            showToast('✅ Desktop notifications enabled successfully!', 'success');
          }
        }).catch(() => {});
      } catch (e) {}
    }
  }
}

function startTitleBlinking(senderName) {
  stopTitleBlinking();
  let isBlinking = false;
  titleBlinkInterval = setInterval(() => {
    document.title = isBlinking ? `⚡ (NEW MSG) ${senderName}` : originalDocumentTitle;
    isBlinking = !isBlinking;
  }, 1000);
}

function stopTitleBlinking() {
  if (titleBlinkInterval) {
    clearInterval(titleBlinkInterval);
    titleBlinkInterval = null;
  }
  document.title = originalDocumentTitle;
}

window.addEventListener('focus', () => {
  stopTitleBlinking();
});

function showAutoDesktopNotification(sender, messageText) {
  if ('Notification' in window && Notification.permission === 'granted') {
    try {
      const notif = new Notification(`💬 SeeChat: Message from ${sender}`, {
        body: messageText,
        tag: 'seechat-alert',
        renotify: true
      });
      notif.onclick = function () {
        window.focus();
        if (sender) selectChat('user', sender);
        notif.close();
      };
    } catch (e) {}
  }
}

socket.on('connect', () => {
  checkAuthSession();
});

if (userSearchInput) {
  userSearchInput.addEventListener('input', () => {
    renderUsersList();
  });
}

document.querySelectorAll('.tab-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    activeTab = btn.dataset.tab;
    
    if (activeTab === 'admin') {
      if (fullAdminPanel) fullAdminPanel.classList.remove('hidden');
      socket.emit('admin_get_users');
      return;
    }

    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach((tc) => tc.classList.remove('active'));

    btn.classList.add('active');
    const targetTabEl = document.getElementById(`tab-${activeTab}`);
    if (targetTabEl) targetTabEl.classList.add('active');
  });
});

if (btnCloseAdminPanel) {
  btnCloseAdminPanel.addEventListener('click', () => {
    if (fullAdminPanel) fullAdminPanel.classList.add('hidden');
  });
}

document.addEventListener('click', () => {
  if (contextMenu) contextMenu.classList.add('hidden');
  if (groupContextMenu) groupContextMenu.classList.add('hidden');
});

// --- 3. RIGHT CLICK ACTIONS FOR TEAM MEMBERS ---
if (ctxMuteUser) {
  ctxMuteUser.addEventListener('click', () => {
    if (!selectedRightClickUser) return;
    const idx = mutedUsers.indexOf(selectedRightClickUser);
    if (idx > -1) {
      mutedUsers.splice(idx, 1);
      showToast(`Unmuted notifications from ${selectedRightClickUser}`, 'info');
    } else {
      mutedUsers.push(selectedRightClickUser);
      showToast(`Muted notifications from ${selectedRightClickUser}`, 'info');
    }
    localStorage.setItem('seechat_muted_users', JSON.stringify(mutedUsers));
    renderUsersList();
  });
}

if (ctxPinUser) {
  ctxPinUser.addEventListener('click', () => {
    if (!selectedRightClickUser) return;
    const idx = pinnedUsers.indexOf(selectedRightClickUser);
    if (idx > -1) {
      pinnedUsers.splice(idx, 1);
    } else {
      pinnedUsers.push(selectedRightClickUser);
    }
    localStorage.setItem('seechat_pinned_users', JSON.stringify(pinnedUsers));
    renderUsersList();
  });
}

if (ctxAddToGroup) {
  ctxAddToGroup.addEventListener('click', () => {
    if (selectedRightClickUser) {
      if (broadcastGroups.length === 0) {
        showToast(`No existing groups found. Creating new group with ${selectedRightClickUser}.`, 'info');
        openGroupModalWithPreselect(selectedRightClickUser);
      } else if (broadcastGroups.length === 1) {
        socket.emit('add_member_to_group', { group_name: broadcastGroups[0].group_name, username: selectedRightClickUser });
      } else {
        const groupOptions = broadcastGroups.map(g => g.group_name).join(', ');
        const choice = prompt(`Add ${selectedRightClickUser} to group:\nAvailable: ${groupOptions}`, broadcastGroups[0].group_name);
        if (choice && choice.trim()) {
          socket.emit('add_member_to_group', { group_name: choice.trim(), username: selectedRightClickUser });
        }
      }
    }
  });
}

function openClearChatModal(targetName) {
  if (!clearChatModal) return;
  pendingClearTarget = targetName;
  clearChatModal.classList.remove('hidden');
}

function closeClearChatModal() {
  if (!clearChatModal) return;
  pendingClearTarget = null;
  clearChatModal.classList.add('hidden');
}

if (btnCancelClearChat) btnCancelClearChat.addEventListener('click', closeClearChatModal);

if (btnConfirmClearChat) {
  btnConfirmClearChat.addEventListener('click', () => {
    if (pendingClearTarget) {
      const target = pendingClearTarget;
      const chatKey = currentTarget && currentTarget.type === 'group' && currentTarget.name === target ? `bcast_${target}` : target;
      chatHistories[chatKey] = [];
      socket.emit('clear_chat_history', { target });
      if (currentTarget && currentTarget.name === target) {
        renderMessages();
      }
      closeClearChatModal();
    }
  });
}

if (ctxClearUserChat) {
  ctxClearUserChat.addEventListener('click', () => {
    if (selectedRightClickUser) {
      openClearChatModal(selectedRightClickUser);
    }
  });
}

if (btnPingDesk) {
  btnPingDesk.addEventListener('click', () => {
    if (currentTarget && currentTarget.type === 'user') {
      sendCallToDeskPing(currentTarget.name);
    }
  });
}

function sendCallToDeskPing(targetUser) {
  const alertText = `📢 URGENT PING: Please come to ${myUsername}'s desk right now!`;
  socket.emit('send_direct_message', { recipient: targetUser, text: alertText });
  showToast(`Urgent Call to Desk alert sent to ${targetUser}!`, 'success');
}

// Group Context Menu Actions
if (ctxRenameGroup) {
  ctxRenameGroup.addEventListener('click', () => {
    if (selectedRightClickGroup) {
      promptRenameGroup(selectedRightClickGroup.group_name);
    }
  });
}

if (ctxEditGroupMembers) {
  ctxEditGroupMembers.addEventListener('click', () => {
    if (selectedRightClickGroup) {
      openGroupModalForEdit(selectedRightClickGroup);
    }
  });
}

if (ctxDeleteGroup) {
  ctxDeleteGroup.addEventListener('click', () => {
    if (selectedRightClickGroup) {
      confirmDeleteGroup(selectedRightClickGroup.group_name);
    }
  });
}

if (btnClearChat) {
  btnClearChat.addEventListener('click', () => {
    if (currentTarget) {
      openClearChatModal(currentTarget.name);
    }
  });
}

if (btnRenameGroup) {
  btnRenameGroup.addEventListener('click', () => {
    if (currentTarget && currentTarget.type === 'group') {
      promptRenameGroup(currentTarget.name);
    }
  });
}

if (btnDeleteGroup) {
  btnDeleteGroup.addEventListener('click', () => {
    if (currentTarget && currentTarget.type === 'group') {
      confirmDeleteGroup(currentTarget.name);
    }
  });
}

function promptRenameGroup(oldName) {
  const newName = prompt(`Enter new name for group "${oldName}":`, oldName);
  if (newName && newName.trim() && newName.trim() !== oldName) {
    socket.emit('rename_broadcast_group', { old_name: oldName, new_name: newName.trim() });
    if (currentTarget && currentTarget.name === oldName) {
      currentTarget.name = newName.trim();
      targetTitle.textContent = newName.trim();
    }
  }
}

function confirmDeleteGroup(groupName) {
  if (confirm(`Are you sure you want to delete group "${groupName}"?`)) {
    socket.emit('delete_broadcast_group', { group_name: groupName });
    if (currentTarget && currentTarget.name === groupName) {
      currentTarget = null;
      targetTitle.textContent = 'Select a team member or group';
      targetAvatar.textContent = '?';
      chatHeaderActions.classList.add('hidden');
      chatInputBar.classList.add('hidden');
      emptyChatPlaceholder.classList.remove('hidden');
      messagesList.innerHTML = '';
    }
  }
}

// --- 4. SOCKET EVENTS & CHAT REQUEST HANDLERS ---
socket.on('online_users_list', (users) => {
  onlineUsers = users.filter((u) => u.username !== myUsername);
  if (onlineCountEl) onlineCountEl.textContent = onlineUsers.length;
  renderUsersList();
});

socket.on('broadcast_groups_list', (groups) => {
  broadcastGroups = groups;
  renderGroupsList();
});

socket.on('chat_request_status_result', ({ targetUser, status }) => {
  currentReqStatus = status;
  if (currentTarget && currentTarget.name === targetUser) {
    renderChatRequestOverlay(targetUser, status);
  }
});

socket.on('incoming_chat_request', ({ sender }) => {
  showToast(`📩 Chat Request received from ${sender}!`, 'info');
  if (currentTarget && currentTarget.name === sender) {
    selectChat('user', sender);
  }
});

socket.on('chat_request_responded', ({ responder, action, status }) => {
  if (action === 'accept') {
    showToast(`🎉 ${responder} accepted your chat request! You can now chat.`, 'success');
  } else {
    showToast(`ℹ️ ${responder} declined the chat request.`, 'info');
  }
  if (currentTarget && currentTarget.name === responder) {
    selectChat('user', responder);
  }
});

socket.on('message_send_failed', ({ error }) => {
  showToast(error, 'error');
});

function flushPendingDeliveryAcks() {
  if (document.hidden || !document.hasFocus()) return;
  if (pendingDeliveryAcks.size > 0) {
    pendingDeliveryAcks.forEach((msgId) => {
      socket.emit('message_delivered_ack', { message_id: msgId });
    });
    pendingDeliveryAcks.clear();
  }
}

// INCOMING DIRECT MESSAGE HANDLER
socket.on('receive_direct_message', (msg) => {
  if (msg.recipient !== myUsername && msg.sender !== myUsername && !msg.is_broadcast) {
    return;
  }

  liveAnimatedMsgIds.add(msg.message_id);

  const partner = msg.is_broadcast ? msg.broadcast_group : (msg.sender === myUsername ? msg.recipient : msg.sender);
  userActivityTimestamps[partner] = Date.now();

  // Send Delivered ACK back to server ONLY if recipient window is active & visible
  if (msg.recipient === myUsername && msg.message_id) {
    if (!document.hidden && document.hasFocus()) {
      socket.emit('message_delivered_ack', { message_id: msg.message_id });
    } else {
      pendingDeliveryAcks.add(msg.message_id);
    }
  }

  const chatKey = msg.is_broadcast ? `bcast_${msg.broadcast_group}` : (msg.sender === myUsername ? msg.recipient : msg.sender);
  if (!chatHistories[chatKey]) chatHistories[chatKey] = [];
  
  if (!chatHistories[chatKey].some(m => m.message_id === msg.message_id)) {
    chatHistories[chatKey].push(msg);
  }

  const targetName = msg.is_broadcast ? msg.broadcast_group : (msg.sender === myUsername ? msg.recipient : msg.sender);
  
  if (currentTarget && currentTarget.name === targetName) {
    renderMessages();
    if (msg.sender !== myUsername && !msg.is_broadcast) {
      if (!document.hidden && document.hasFocus()) {
        socket.emit('mark_conversation_read', { targetUser: msg.sender });
        unreadCounts[msg.sender] = 0;
        renderUsersList();
      }
    }
  } else if (msg.sender !== myUsername && !msg.is_broadcast) {
    unreadCounts[msg.sender] = (unreadCounts[msg.sender] || 0) + 1;
    renderUsersList();
  }

  if (msg.sender !== myUsername && !mutedUsers.includes(msg.sender)) {
    if (document.hidden || !document.hasFocus()) {
      startTitleBlinking(msg.sender);
      showAutoDesktopNotification(msg.sender, msg.message);
    }
  }
});

socket.on('message_status_updated', ({ message_id, status }) => {
  for (const chatKey in chatHistories) {
    const msg = chatHistories[chatKey].find((m) => m.message_id === message_id);
    if (msg) {
      msg.status = status;
      break;
    }
  }
  const labelEl = document.getElementById(`msg-status-${message_id}`);
  if (labelEl) {
    const timeText = labelEl.textContent.split('•')[0].trim();
    labelEl.textContent = `${timeText} • Delivered`;
    labelEl.className = 'msg-status-label msg-status-delivered';
  }
});

socket.on('messages_marked_read', ({ reader, message_ids }) => {
  if (message_ids && Array.isArray(message_ids)) {
    message_ids.forEach((id) => {
      for (const chatKey in chatHistories) {
        const msg = chatHistories[chatKey].find((m) => m.message_id === id);
        if (msg) msg.status = 'read';
      }
      const labelEl = document.getElementById(`msg-status-${id}`);
      if (labelEl) {
        const timeText = labelEl.textContent.split('•')[0].trim();
        labelEl.textContent = `${timeText} • Read`;
        labelEl.className = 'msg-status-label msg-status-read';
      }
    });
  }
});

socket.on('message_edited', ({ message_id, new_text, is_edited, edited_at }) => {
  for (const chatKey in chatHistories) {
    const msg = chatHistories[chatKey].find((m) => m.message_id === message_id);
    if (msg) {
      msg.message = new_text;
      msg.is_edited = 1;
      msg.edited_at = edited_at;
      break;
    }
  }
  renderMessages();
});

socket.on('message_deleted', ({ message_id, is_deleted, deleted_at }) => {
  for (const chatKey in chatHistories) {
    const msg = chatHistories[chatKey].find((m) => m.message_id === message_id);
    if (msg) {
      msg.is_deleted = 1;
      msg.message = 'Message deleted';
      msg.reactions = [];
      break;
    }
  }
  renderMessages();
});

socket.on('message_reactions_updated', ({ message_id, reactions }) => {
  for (const chatKey in chatHistories) {
    const msg = chatHistories[chatKey].find((m) => m.message_id === message_id);
    if (msg) {
      msg.reactions = reactions;
      break;
    }
  }
  const reactionsBarEl = document.getElementById(`msg-reactions-${message_id}`);
  if (reactionsBarEl) {
    renderReactionsBarEl(reactionsBarEl, message_id, reactions);
  }
});

socket.on('user_typing', ({ sender }) => {
  if (currentTarget && currentTarget.name === sender && typingIndicator) {
    if (typingUsername) typingUsername.textContent = sender;
    typingIndicator.classList.remove('hidden');
  }
});

socket.on('user_stop_typing', ({ sender }) => {
  if (currentTarget && currentTarget.name === sender && typingIndicator) {
    typingIndicator.classList.add('hidden');
  }
});

socket.on('receive_studio_announcement', ({ sender, message }) => {
  showToast(`📢 Announcement from ${sender}: "${message}"`, 'info');
});

socket.on('chat_cleared', ({ target }) => {
  const chatKey = `bcast_${target}` in chatHistories ? `bcast_${target}` : target;
  chatHistories[chatKey] = [];
  if (currentTarget && currentTarget.name === target) {
    renderMessages();
  }
});

socket.on('message_sent_confirm', (msg) => {
  const chatKey = msg.recipient;
  if (!chatHistories[chatKey]) chatHistories[chatKey] = [];
  msg.status = 'sent';
  chatHistories[chatKey].push(msg);
  if (currentTarget && currentTarget.name === msg.recipient) {
    renderMessages();
  }
});

socket.on('broadcast_sent_confirm', ({ group_name, text, timestamp }) => {
  const chatKey = `bcast_${group_name}`;
  if (!chatHistories[chatKey]) chatHistories[chatKey] = [];
  chatHistories[chatKey].push({
    message_id: `bcast_${Date.now()}`,
    sender: myUsername,
    recipient: group_name,
    message: text,
    timestamp: timestamp,
    status: 'sent',
    is_self_broadcast: true
  });

  if (currentTarget && currentTarget.name === group_name) {
    renderMessages();
  }
});

socket.on('chat_history', ({ targetUser, history, unread_counts }) => {
  chatHistories[targetUser] = history;
  if (unread_counts) unreadCounts = unread_counts;
  renderUsersList();
  if (currentTarget && currentTarget.name === targetUser) {
    renderMessages();
    socket.emit('mark_conversation_read', { targetUser: targetUser });
    unreadCounts[targetUser] = 0;
    renderUsersList();
  }
});

// --- ADMIN PANEL SOCKET EVENT LISTENERS & REAL BACKEND DATA ---
socket.on('server_health_data', (data) => {
  if (shPython) shPython.textContent = data.python_server === 'Running' ? '🟢 Running' : '🔴 Stopped';
  if (shSocket) shSocket.textContent = data.socket_io === 'Connected' ? '🟢 Connected' : '🔴 Disconnected';
  if (shDb) shDb.textContent = data.sqlite_db || '🟢 Connected';
  if (shCsv) shCsv.textContent = data.csv_logger === 'Running' ? '🟢 Running' : '🔴 Write Failed';
  if (shConns) shConns.textContent = data.active_connections || 0;
  if (shUptime) shUptime.textContent = data.uptime || '0h 0m';
});

socket.on('admin_action_response', ({ success, message, action }) => {
  showToast(message, success ? 'success' : 'error');
  
  if (action === 'broadcast' && success && adminNoticeInput) {
    adminNoticeInput.value = '';
    btnSendStudioNotice.classList.add('btn-disabled-state');
  }
  if (action === 'add_user' && success && adminAddUsername) {
    adminAddUsername.value = '';
    btnAdminAddUser.classList.add('btn-disabled-state');
  }
});

socket.on('admin_users_list', (users) => {
  if (!adminUsersTableBody) return;
  adminUsersTableBody.innerHTML = '';

  users.forEach((u) => {
    const tr = document.createElement('tr');
    const isDisabled = Boolean(u.is_disabled);
    const isOnline = Boolean(u.is_online);

    let statusBadgeHtml = '';
    if (isDisabled) {
      statusBadgeHtml = '<span class="status-badge disabled">🔴 Disabled</span>';
    } else if (isOnline) {
      statusBadgeHtml = '<span class="status-badge online">🟢 Online</span>';
    } else {
      statusBadgeHtml = '<span class="status-badge offline">⚪ Offline</span>';
    }

    const isAdmin = u.role === 'admin';
    const isSelf = u.username === myUsername;

    tr.innerHTML = `
      <td><strong>${escapeHtml(u.username)}</strong></td>
      <td>
        <select class="admin-role-select" data-uname="${escapeHtml(u.username)}" ${isSelf ? 'disabled' : ''}>
          <option value="user" ${!isAdmin ? 'selected' : ''}>User</option>
          <option value="admin" ${isAdmin ? 'selected' : ''}>Admin</option>
        </select>
      </td>
      <td><code>${escapeHtml(u.ip_address || '127.0.0.1')}</code></td>
      <td>${statusBadgeHtml}</td>
      <td>
        <div style="display:flex; gap:8px; align-items:center;">
          ${!isSelf ? `
            <button class="btn btn-sm ${isDisabled ? 'btn-warning' : 'btn-secondary'} btn-admin-disable-toggle" data-uname="${escapeHtml(u.username)}" data-disabled="${isDisabled}">${isDisabled ? 'Enable' : 'Disable'}</button>
            <button class="btn btn-sm btn-danger btn-admin-delete" data-uname="${escapeHtml(u.username)}">Delete User</button>
          ` : '<span style="color:#a6e3a1; font-weight:700; font-size:0.84rem;">Current Session</span>'}
        </div>
      </td>
    `;
    adminUsersTableBody.appendChild(tr);
  });

  document.querySelectorAll('.admin-role-select').forEach((sel) => {
    sel.addEventListener('change', () => {
      const targetUser = sel.dataset.uname;
      const targetRole = sel.value;
      if (targetUser) {
        socket.emit('admin_toggle_user_role', { username: targetUser, role: targetRole });
      }
    });
  });

  document.querySelectorAll('.btn-admin-disable-toggle').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetUser = btn.dataset.uname;
      const currentlyDisabled = btn.dataset.disabled === 'true';
      const actionWord = currentlyDisabled ? 'enable' : 'disable';

      if (targetUser && confirm(`Confirm ${actionWord}ing account for "${targetUser}"?`)) {
        socket.emit('admin_toggle_user_disabled', { username: targetUser });
      }
    });
  });

  document.querySelectorAll('.btn-admin-delete').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetUser = btn.dataset.uname;
      if (targetUser && confirm(`Are you sure you want to delete user account "${targetUser}"?`)) {
        socket.emit('admin_delete_user', { username: targetUser });
      }
    });
  });
});

// FORM INPUT BUTTON STATE VALIDATIONS
if (adminNoticeInput && btnSendStudioNotice) {
  adminNoticeInput.addEventListener('input', () => {
    if (adminNoticeInput.value.trim()) {
      btnSendStudioNotice.classList.remove('btn-disabled-state');
    } else {
      btnSendStudioNotice.classList.add('btn-disabled-state');
    }
  });
}

if (adminAddUsername && btnAdminAddUser) {
  adminAddUsername.addEventListener('input', () => {
    if (adminAddUsername.value.trim()) {
      btnAdminAddUser.classList.remove('btn-disabled-state');
    } else {
      btnAdminAddUser.classList.add('btn-disabled-state');
    }
  });
}

if (btnAdminAddUser) {
  btnAdminAddUser.addEventListener('click', () => {
    const uname = adminAddUsername.value.trim();
    const role = adminAddRole.value;
    if (!uname) {
      showToast("Please enter a valid username.", "error");
      return;
    }
    socket.emit('admin_add_user', { username: uname, role: role });
  });
}

if (btnSendStudioNotice) {
  btnSendStudioNotice.addEventListener('click', () => {
    const notice = adminNoticeInput.value.trim();
    if (!notice) {
      showToast("Please enter an announcement text.", "error");
      return;
    }
    socket.emit('admin_broadcast_announcement', { notice });
  });
}

// --- 5. UI RENDERING & CHAT REQUEST OVERLAY ---
function renderUsersList() {
  if (!usersListEl) return;
  usersListEl.innerHTML = '';
  const filterQuery = userSearchInput ? userSearchInput.value.toLowerCase().trim() : '';
  let filtered = onlineUsers.filter(u => u.username.toLowerCase().includes(filterQuery));

  filtered.sort((a, b) => {
    const aPin = pinnedUsers.includes(a.username);
    const bPin = pinnedUsers.includes(b.username);
    if (aPin && !bPin) return -1;
    if (!aPin && bPin) return 1;
    if (aPin && bPin) return a.username.localeCompare(b.username);

    const aUnread = unreadCounts[a.username] || 0;
    const bUnread = unreadCounts[b.username] || 0;
    if (aUnread > 0 && bUnread === 0) return -1;
    if (aUnread === 0 && bUnread > 0) return 1;

    const aTime = userActivityTimestamps[a.username] || 0;
    const bTime = userActivityTimestamps[b.username] || 0;
    if (aTime !== bTime) {
      return bTime - aTime;
    }

    return a.username.localeCompare(b.username);
  });

  if (filtered.length === 0) {
    usersListEl.innerHTML = '<li class="empty-state">No matching team members</li>';
    return;
  }

  filtered.forEach((u) => {
    const isPinned = pinnedUsers.includes(u.username);
    const isMuted = mutedUsers.includes(u.username);
    const unreadCnt = unreadCounts[u.username] || 0;
    const hasUnread = unreadCnt > 0;
    const unreadBadgeHtml = hasUnread ? `<span class="unread-badge">${unreadCnt > 99 ? '99+' : unreadCnt}</span>` : '';
    const moodHtml = `<span class="user-mood" style="font-size:0.75rem; color:var(--text-muted); opacity:0.8; margin-left:6px;">${escapeHtml(u.mood_status || 'Available')}</span>`;

    const li = document.createElement('li');
    li.className = `list-item ${currentTarget && currentTarget.name === u.username ? 'active' : ''} ${isPinned ? 'pinned' : ''} ${hasUnread ? 'has-unread' : ''}`;

    li.innerHTML = `
      <div class="item-avatar">${u.username.charAt(0).toUpperCase()}</div>
      <div class="item-details">
        <div class="item-name" style="${hasUnread ? 'font-weight:700; color:#89b4fa;' : ''}">${escapeHtml(u.username)} ${moodHtml} ${isPinned ? '📌' : ''} ${isMuted ? '🔕' : ''}</div>
      </div>
      ${unreadBadgeHtml}
    `;
    
    li.addEventListener('click', () => selectChat('user', u.username));
    li.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (groupContextMenu) groupContextMenu.classList.add('hidden');
      selectedRightClickUser = u.username;

      if (ctxPinUser) ctxPinUser.textContent = isPinned ? '📌 Unpin Member' : '📌 Pin / Unpin to Top';
      if (ctxMuteUser) ctxMuteUser.textContent = isMuted ? '🔔 Unmute Notifications' : '🔕 Mute / Unmute Notifications';

      if (contextMenu) {
        contextMenu.style.top = `${e.pageY}px`;
        contextMenu.style.left = `${e.pageX}px`;
        contextMenu.classList.remove('hidden');
      }
    });

    usersListEl.appendChild(li);
  });
}

function renderGroupsList() {
  if (!groupsListEl) return;
  groupsListEl.innerHTML = '';
  if (broadcastGroups.length === 0) {
    groupsListEl.innerHTML = '<li class="empty-state">No groups created</li>';
    return;
  }

  broadcastGroups.forEach((g) => {
    const li = document.createElement('li');
    li.className = `list-item ${currentTarget && currentTarget.name === g.group_name ? 'active' : ''}`;
    li.innerHTML = `
      <div class="item-avatar" style="background:#313244;">👥</div>
      <div class="item-details">
        <div class="item-name">${escapeHtml(g.group_name)}</div>
        <div class="item-subtext">${g.members.length} members</div>
      </div>
    `;
    
    li.addEventListener('click', () => selectChat('group', g.group_name, g.members));

    li.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (contextMenu) contextMenu.classList.add('hidden');
      selectedRightClickGroup = g;

      if (groupContextMenu) {
        groupContextMenu.style.top = `${e.pageY}px`;
        groupContextMenu.style.left = `${e.pageX}px`;
        groupContextMenu.classList.remove('hidden');
      }
    });

    groupsListEl.appendChild(li);
  });
}

function selectChat(type, name, members = []) {
  currentTarget = { type, name, members };

  if (typingIndicator) typingIndicator.classList.add('hidden');

  if (type === 'user') {
    unreadCounts[name] = 0;
    socket.emit('mark_conversation_read', { targetUser: name });
  }

  renderUsersList();
  renderGroupsList();

  if (targetAvatar) targetAvatar.textContent = type === 'group' ? '👥' : name.charAt(0).toUpperCase();
  if (targetTitle) targetTitle.textContent = name;

  if (chatHeaderActions) chatHeaderActions.classList.remove('hidden');
  if (type === 'group') {
    if (groupHeaderActions) groupHeaderActions.classList.remove('hidden');
    if (btnPingDesk) btnPingDesk.classList.add('hidden');
    if (chatRequestContainer) chatRequestContainer.classList.add('hidden');
    if (chatInputBar) chatInputBar.classList.remove('hidden');
    if (emptyChatPlaceholder) emptyChatPlaceholder.classList.add('hidden');
    renderMessages();
  } else {
    if (groupHeaderActions) groupHeaderActions.classList.add('hidden');
    if (btnPingDesk) btnPingDesk.classList.remove('hidden');
    
    socket.emit('get_chat_request_status', { targetUser: name });
    socket.emit('get_chat_history', { targetUser: name });
  }

  const chatKey = type === 'group' ? `bcast_${name}` : name;
  if (!chatHistories[chatKey]) chatHistories[chatKey] = [];
}

function renderChatRequestOverlay(targetUser, status) {
  if (!chatRequestContainer || !currentTarget || currentTarget.name !== targetUser || currentTarget.type !== 'user') return;

  if (status === 'accepted') {
    chatRequestContainer.classList.add('hidden');
    if (chatInputBar) chatInputBar.classList.remove('hidden');
    if (emptyChatPlaceholder) emptyChatPlaceholder.classList.add('hidden');
    renderMessages();
    return;
  }

  if (chatInputBar) chatInputBar.classList.add('hidden');
  if (emptyChatPlaceholder) emptyChatPlaceholder.classList.add('hidden');
  chatRequestContainer.classList.remove('hidden');
  requestActionsArea.innerHTML = '';

  if (status === 'pending_out') {
    requestCardTitle.textContent = "⌛ Chat Request Pending";
    requestCardSubtext.textContent = `Your chat request to ${targetUser} is waiting for approval. You can message once accepted.`;
  } else if (status === 'pending_in') {
    requestCardTitle.textContent = "📩 Incoming Chat Request";
    requestCardSubtext.textContent = `${targetUser} sent you a chat request. Accept to start messaging.`;
    
    const btnAccept = document.createElement('button');
    btnAccept.className = 'btn btn-primary';
    btnAccept.style.marginRight = '8px';
    btnAccept.textContent = '✅ Accept Request';
    btnAccept.onclick = () => socket.emit('respond_chat_request', { partner: targetUser, action: 'accept' });

    const btnDecline = document.createElement('button');
    btnDecline.className = 'btn btn-secondary';
    btnDecline.textContent = '❌ Decline';
    btnDecline.onclick = () => socket.emit('respond_chat_request', { partner: targetUser, action: 'decline' });

    requestActionsArea.appendChild(btnAccept);
    requestActionsArea.appendChild(btnDecline);
  } else {
    requestCardTitle.textContent = "📩 Chat Request Required";
    requestCardSubtext.textContent = `Send a chat request to ${targetUser} to start messaging.`;
    
    const btnSendReq = document.createElement('button');
    btnSendReq.className = 'btn btn-primary';
    btnSendReq.textContent = '📩 Send Chat Request';
    btnSendReq.onclick = () => socket.emit('send_chat_request', { recipient: targetUser });

    requestActionsArea.appendChild(btnSendReq);
  }
}

function getEmojiOnlyInfo(text) {
  if (!text) return { type: 'normal' };
  const trimmed = text.trim();
  const emojiRegex = /(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])/g;
  const matches = trimmed.match(emojiRegex);
  if (!matches) return { type: 'normal' };
  
  const nonEmojiText = trimmed.replace(emojiRegex, '').replace(/\s+/g, '');
  if (nonEmojiText.length > 0) return { type: 'normal' };

  if (matches.length === 1) {
    return { type: 'single', emoji: matches[0] };
  } else if (matches.length === 2) {
    return { type: 'double' };
  }
  return { type: 'normal' };
}

function getEmojiAnimClass(emoji) {
  if (emoji === '😂' || emoji === '😅') return 'anim-bounce';
  if (emoji === '👍') return 'anim-pop';
  if (emoji === '👏') return 'anim-shake';
  if (emoji === '🎉' || emoji === '🔥') return 'anim-scale';
  return 'anim-pop';
}

function setReplyMessage(msgId, sender, text) {
  clearEditMessage();
  pendingReplyMessage = { id: msgId, sender, text };
  if (replyTargetSender) replyTargetSender.textContent = sender;
  if (replyTargetText) replyTargetText.textContent = `"${text.length > 40 ? text.substring(0, 40) + '...' : text}"`;
  if (replyPreviewBar) replyPreviewBar.classList.remove('hidden');
  if (messageInput) messageInput.focus();
}

function clearReplyMessage() {
  pendingReplyMessage = null;
  if (replyPreviewBar) replyPreviewBar.classList.add('hidden');
}

if (btnCancelReply) {
  btnCancelReply.addEventListener('click', clearReplyMessage);
}

function setEditMessage(msgId, text) {
  clearReplyMessage();
  pendingEditMessage = { id: msgId, text };
  if (editTargetText) editTargetText.textContent = `"${text.length > 40 ? text.substring(0, 40) + '...' : text}"`;
  if (editPreviewBar) editPreviewBar.classList.remove('hidden');
  if (messageInput) {
    messageInput.value = text;
    messageInput.focus();
  }
}

function clearEditMessage() {
  pendingEditMessage = null;
  if (editPreviewBar) editPreviewBar.classList.add('hidden');
}

if (btnCancelEdit) {
  btnCancelEdit.addEventListener('click', () => {
    clearEditMessage();
    if (messageInput) messageInput.value = '';
  });
}

function openDeleteModal(msgId) {
  pendingDeleteMessageId = msgId;
  if (deleteConfirmModal) deleteConfirmModal.classList.remove('hidden');
}

function closeDeleteModal() {
  pendingDeleteMessageId = null;
  if (deleteConfirmModal) deleteConfirmModal.classList.add('hidden');
}

if (btnCancelDelete) btnCancelDelete.addEventListener('click', closeDeleteModal);
if (btnConfirmDelete) {
  btnConfirmDelete.addEventListener('click', () => {
    if (pendingDeleteMessageId) {
      socket.emit('delete_message', { message_id: pendingDeleteMessageId });
    }
    closeDeleteModal();
  });
}

function positionEmojiPicker() {
  if (!emojiPicker || !btnToggleEmoji) return;
  const composerWrapper = document.getElementById('composer-wrapper') || document.getElementById('main-chat-area');
  if (!composerWrapper) return;

  const wrapperRect = composerWrapper.getBoundingClientRect();
  const btnRect = btnToggleEmoji.getBoundingClientRect();

  let leftOffset = btnRect.left - wrapperRect.left - 6;
  const pickerWidth = 250;
  if (leftOffset < 8) leftOffset = 8;
  if (leftOffset + pickerWidth > wrapperRect.width - 8) {
    leftOffset = wrapperRect.width - pickerWidth - 8;
  }

  emojiPicker.style.position = 'absolute';
  emojiPicker.style.bottom = '100%';
  emojiPicker.style.marginBottom = '8px';
  emojiPicker.style.left = `${leftOffset}px`;
  emojiPicker.style.right = 'auto';
  emojiPicker.style.top = 'auto';
  emojiPicker.style.zIndex = '1500';
}

function renderReactionsBarEl(barEl, messageId, reactions) {
  if (!barEl) return;
  barEl.innerHTML = '';
  if (!reactions || reactions.length === 0) return;

  reactions.forEach((r) => {
    const isMyReaction = r.users && r.users.includes(myUsername);
    const badge = document.createElement('div');
    badge.className = `reaction-badge ${isMyReaction ? 'active-user' : ''}`;
    badge.innerHTML = `<span>${r.emoji}</span><span>${r.count}</span>`;
    badge.addEventListener('click', (e) => {
      e.stopPropagation();
      socket.emit('toggle_message_reaction', { message_id: messageId, emoji: r.emoji });
    });
    barEl.appendChild(badge);
  });
}

function renderMessages() {
  if (!currentTarget || !messagesList) return;
  messagesList.innerHTML = '';

  const chatKey = currentTarget.type === 'group' ? `bcast_${currentTarget.name}` : currentTarget.name;
  const msgs = chatHistories[chatKey] || [];

  msgs.forEach((m) => {
    const isSentByMe = m.sender === myUsername;

    const wrapper = document.createElement('div');
    wrapper.className = `msg-bubble-wrapper ${isSentByMe ? 'sent' : 'received'}`;

    const bubble = document.createElement('div');

    const timeStr = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
    const editedTag = m.is_edited ? ' • Edited' : '';
    
    let statusLabelHtml = '';
    if (isSentByMe && currentTarget.type === 'user') {
      const st = m.status === 'read' || m.status === 'seen' ? 'Read' : (m.status === 'delivered' ? 'Delivered' : 'Sent');
      const stClass = m.status === 'read' || m.status === 'seen' ? 'msg-status-read' : (m.status === 'delivered' ? 'msg-status-delivered' : 'msg-status-sent');
      statusLabelHtml = `<span class="msg-status-label ${stClass}" id="msg-status-${m.message_id}">${timeStr}${editedTag} • ${st}</span>`;
    } else {
      statusLabelHtml = `<span class="msg-status-label">${timeStr}${editedTag}</span>`;
    }

    let msgBodyHtml = '';
    let extraBubbleClass = '';

    if (m.is_deleted) {
      msgBodyHtml = `<div class="msg-text" style="font-style:italic; opacity:0.75;">Message deleted</div>`;
    } else {
      const emojiInfo = getEmojiOnlyInfo(m.message);

      if (emojiInfo.type === 'single') {
        extraBubbleClass = 'emoji-msg-single';
        let animClass = '';
        if (liveAnimatedMsgIds.has(m.message_id)) {
          animClass = getEmojiAnimClass(emojiInfo.emoji);
          liveAnimatedMsgIds.delete(m.message_id);
        }
        msgBodyHtml = `<div class="msg-text"><span class="single-emoji-display ${animClass}">${escapeHtml(m.message)}</span></div>`;
      } else if (emojiInfo.type === 'double') {
        extraBubbleClass = 'emoji-msg-double';
        msgBodyHtml = `<div class="msg-text"><span class="double-emoji-display">${escapeHtml(m.message)}</span></div>`;
      } else {
        msgBodyHtml = `<div class="msg-text">${escapeHtml(m.message).replace(/\n/g, '<br>')}</div>`;
      }
    }

    let quoteRefHtml = '';
    if (m.reply_preview) {
      quoteRefHtml = `
        <div class="msg-quote-ref">
          <span class="quote-sender">${escapeHtml(m.reply_preview.sender)}</span>
          <span class="quote-text">${escapeHtml(m.reply_preview.message)}</span>
        </div>
      `;
    }

    bubble.className = `msg-bubble ${isSentByMe ? 'sent' : 'received'} ${extraBubbleClass}`;

    bubble.innerHTML = `
      ${!m.is_deleted ? '<button class="msg-action-btn" title="Actions">⋯</button>' : ''}
      ${!isSentByMe && currentTarget.type === 'group' ? `<div class="msg-sender-name">${escapeHtml(m.sender)}</div>` : ''}
      ${quoteRefHtml}
      ${msgBodyHtml}
      <div class="msg-meta">
        ${statusLabelHtml}
      </div>
    `;

    if (!m.is_deleted) {
      const actionBtn = bubble.querySelector('.msg-action-btn');
      if (actionBtn) {
        actionBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          document.querySelectorAll('.msg-action-popup, .reaction-picker-popup').forEach((p) => p.remove());

          const popup = document.createElement('div');
          popup.className = 'msg-action-popup';
          
          const itemReply = document.createElement('div');
          itemReply.className = 'msg-action-item';
          itemReply.innerHTML = '<span>💬</span><span>Reply</span>';
          itemReply.onclick = (eEv) => {
            eEv.stopPropagation();
            popup.remove();
            setReplyMessage(m.message_id, m.sender, m.message);
          };

          const itemReact = document.createElement('div');
          itemReact.className = 'msg-action-item';
          itemReact.innerHTML = '<span>😊</span><span>React</span>';
          itemReact.onclick = (eEv) => {
            eEv.stopPropagation();
            popup.remove();
            
            const reactPicker = document.createElement('div');
            reactPicker.className = 'reaction-picker-popup';
            
            const currentEmojis = ['😊', '👍', '😂', '😅', '🤝', '👏', '🎉', '🙏', '⚠️', '💼', '📌', '✅', '❌', '🕒', '⏳', '📞', '📂', '💻', '⭐', '❓', '☕', '🟢'];
            currentEmojis.forEach((em) => {
              const emSpan = document.createElement('span');
              emSpan.className = 'reaction-picker-emoji';
              emSpan.textContent = em;
              emSpan.onclick = (emEv) => {
                emEv.stopPropagation();
                reactPicker.remove();
                addRecentEmoji(em);
                socket.emit('toggle_message_reaction', { message_id: m.message_id, emoji: em });
              };
              reactPicker.appendChild(emSpan);
            });

            wrapper.appendChild(reactPicker);

            if (messagesContainer) {
              const containerRect = messagesContainer.getBoundingClientRect();
              const bubbleRect = bubble.getBoundingClientRect();

              if (bubbleRect.bottom + 160 > containerRect.bottom && bubbleRect.top - 160 > containerRect.top) {
                reactPicker.style.bottom = '100%';
                reactPicker.style.top = 'auto';
                reactPicker.style.marginBottom = '6px';
              } else {
                reactPicker.style.top = '100%';
                reactPicker.style.bottom = 'auto';
                reactPicker.style.marginTop = '6px';
              }

              if (isSentByMe) {
                reactPicker.style.right = '0px';
                reactPicker.style.left = 'auto';
              } else {
                reactPicker.style.left = '0px';
                reactPicker.style.right = 'auto';
              }
            }

            const closeReactPicker = (cEv) => {
              if (!reactPicker.contains(cEv.target)) {
                reactPicker.remove();
                document.removeEventListener('click', closeReactPicker);
              }
            };
            setTimeout(() => document.addEventListener('click', closeReactPicker), 10);
          };

          popup.appendChild(itemReply);
          popup.appendChild(itemReact);

          // Add Edit & Delete options ONLY for sender of message
          if (isSentByMe && !m.is_deleted) {
            const itemEdit = document.createElement('div');
            itemEdit.className = 'msg-action-item';
            itemEdit.innerHTML = '<span>✏️</span><span>Edit</span>';
            itemEdit.onclick = (eEv) => {
              eEv.stopPropagation();
              popup.remove();
              setEditMessage(m.message_id, m.message);
            };

            const itemDelete = document.createElement('div');
            itemDelete.className = 'msg-action-item';
            itemDelete.style.color = '#f38ba8';
            itemDelete.innerHTML = '<span>🗑️</span><span>Delete</span>';
            itemDelete.onclick = (eEv) => {
              eEv.stopPropagation();
              popup.remove();
              openDeleteModal(m.message_id);
            };

            popup.appendChild(itemEdit);
            popup.appendChild(itemDelete);
          }

          wrapper.appendChild(popup);

          const closeActionPopup = (cEv) => {
            if (!popup.contains(cEv.target)) {
              popup.remove();
              document.removeEventListener('click', closeActionPopup);
            }
          };
          setTimeout(() => document.addEventListener('click', closeActionPopup), 10);
        });
      }
    }

    wrapper.appendChild(bubble);

    if (!m.is_deleted) {
      const reactionsBar = document.createElement('div');
      reactionsBar.className = 'msg-reactions-bar';
      reactionsBar.id = `msg-reactions-${m.message_id}`;
      renderReactionsBarEl(reactionsBar, m.message_id, m.reactions);
      wrapper.appendChild(reactionsBar);
    }

    messagesList.appendChild(wrapper);
  });

  if (messagesContainer) messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// --- 6. SEND MESSAGE ---
function sendMessage() {
  if (!messageInput) return;
  const text = messageInput.value.trim();
  if (!text || !currentTarget) return;

  if (pendingEditMessage) {
    socket.emit('edit_message', {
      message_id: pendingEditMessage.id,
      new_text: text
    });
    clearEditMessage();
    messageInput.value = '';
    return;
  }

  const replyToId = pendingReplyMessage ? pendingReplyMessage.id : '';

  if (typingTimer) clearTimeout(typingTimer);
  if (currentTarget.type === 'user') {
    socket.emit('typing_stop', { recipient: currentTarget.name });
    socket.emit('send_direct_message', {
      recipient: currentTarget.name,
      sender: myUsername,
      text,
      reply_to_id: replyToId
    });
  } else if (currentTarget.type === 'group') {
    socket.emit('send_broadcast_message', {
      group_name: currentTarget.name,
      sender: myUsername,
      members: currentTarget.members,
      text,
      reply_to_id: replyToId
    });
  }

  clearReplyMessage();
  messageInput.value = '';
  autoResizeMessageInput();
}

function autoResizeMessageInput() {
  if (!messageInput) return;
  messageInput.style.height = '36px';
  const newHeight = Math.min(Math.max(messageInput.scrollHeight, 36), 160);
  messageInput.style.height = `${newHeight}px`;
  messageInput.style.overflowY = messageInput.scrollHeight > 160 ? 'auto' : 'hidden';

  if (emojiPicker && !emojiPicker.classList.contains('hidden')) {
    positionEmojiPicker();
  }
}

if (btnSend) btnSend.addEventListener('click', sendMessage);
if (messageInput) {
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  messageInput.addEventListener('input', () => {
    autoResizeMessageInput();
    if (currentTarget && currentTarget.type === 'user') {
      socket.emit('typing_start', { recipient: currentTarget.name });
      if (typingTimer) clearTimeout(typingTimer);
      typingTimer = setTimeout(() => {
        socket.emit('typing_stop', { recipient: currentTarget.name });
      }, 2500);
    }
  });
}


if (btnTogglePresets) {
  btnTogglePresets.addEventListener('click', () => { if (presetsBar) presetsBar.classList.toggle('hidden'); });
}

document.querySelectorAll('.preset-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    if (messageInput) {
      messageInput.value += chip.dataset.msg;
      sendMessage();
    }
  });
});

const emojiPickerRecentSection = document.getElementById('emoji-picker-recent-section');
const emojiPickerRecentGrid = document.getElementById('emoji-picker-recent-grid');
const emojiPickerAllGrid = document.getElementById('emoji-picker-all-grid');

function getRecentEmojis() {
  try {
    const data = localStorage.getItem('seechat_recent_emojis');
    return data ? JSON.parse(data) : [];
  } catch (e) {
    return [];
  }
}

function addRecentEmoji(emojiStr) {
  if (!emojiStr) return;
  let list = getRecentEmojis();
  list = list.filter((e) => e !== emojiStr);
  list.unshift(emojiStr);
  list = list.slice(0, 6);
  try {
    localStorage.setItem('seechat_recent_emojis', JSON.stringify(list));
  } catch (e) {}
  renderRecentEmojis();
}

function renderRecentEmojis() {
  if (!emojiPickerRecentSection || !emojiPickerRecentGrid) return;
  const list = getRecentEmojis();
  if (!list || list.length === 0) {
    emojiPickerRecentSection.classList.add('hidden');
    return;
  }
  emojiPickerRecentSection.classList.remove('hidden');
  emojiPickerRecentGrid.innerHTML = '';
  list.forEach((emojiStr) => {
    const span = document.createElement('span');
    span.className = 'emoji-item';
    span.textContent = emojiStr;
    span.addEventListener('click', (e) => {
      e.stopPropagation();
      onEmojiClick(emojiStr);
    });
    emojiPickerRecentGrid.appendChild(span);
  });
}

function onEmojiClick(emojiStr) {
  if (messageInput) {
    messageInput.value += emojiStr;
    addRecentEmoji(emojiStr);
    autoResizeMessageInput();
    messageInput.focus();
  }
}

function openEmojiPicker() {
  if (!emojiPicker) return;
  renderRecentEmojis();
  positionEmojiPicker();
  emojiPicker.classList.remove('hidden');

  setTimeout(() => {
    document.addEventListener('click', handleEmojiPickerOutsideClick);
    document.addEventListener('keydown', handleEmojiPickerEscKey);
  }, 10);
}

function closeEmojiPicker() {
  if (!emojiPicker) return;
  emojiPicker.classList.add('hidden');
  document.removeEventListener('click', handleEmojiPickerOutsideClick);
  document.removeEventListener('keydown', handleEmojiPickerEscKey);
}

function handleEmojiPickerOutsideClick(e) {
  if (!emojiPicker || emojiPicker.classList.contains('hidden')) return;
  if (!emojiPicker.contains(e.target) && !btnToggleEmoji.contains(e.target)) {
    closeEmojiPicker();
  }
}

function handleEmojiPickerEscKey(e) {
  if (e.key === 'Escape' || e.key === 'Esc') {
    if (emojiPicker && !emojiPicker.classList.contains('hidden')) {
      closeEmojiPicker();
    }
  }
}

if (btnToggleEmoji) {
  btnToggleEmoji.addEventListener('click', (e) => {
    e.stopPropagation();
    if (!emojiPicker) return;
    if (emojiPicker.classList.contains('hidden')) {
      openEmojiPicker();
    } else {
      closeEmojiPicker();
    }
  });
}

if (emojiPickerAllGrid) {
  emojiPickerAllGrid.querySelectorAll('.emoji-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.stopPropagation();
      onEmojiClick(item.textContent.trim());
    });
  });
}

window.addEventListener('resize', () => {
  if (emojiPicker && !emojiPicker.classList.contains('hidden')) {
    positionEmojiPicker();
  }
});

renderRecentEmojis();

// Stop blinking document title when browser window gains focus
window.addEventListener('focus', () => {
  stopTitleBlinking();
});

// --- 8. GROUP MODAL & EDITING ---
socket.on('group_action_response', (res) => {
  if (res && res.message) {
    showToast(res.message, res.success ? 'success' : 'error');
  }
});

function renderGroupMembersList() {
  if (!groupMembersChecklist) return;

  if (selectedMembersCount) selectedMembersCount.textContent = selectedGroupMemberSet.size;

  if (selectedMembersChips) {
    selectedMembersChips.innerHTML = '';
    selectedGroupMemberSet.forEach((uname) => {
      const chip = document.createElement('div');
      chip.className = 'member-chip';
      chip.innerHTML = `<span>${escapeHtml(uname)}</span><span class="chip-remove" data-uname="${escapeHtml(uname)}">×</span>`;
      chip.querySelector('.chip-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        selectedGroupMemberSet.delete(uname);
        renderGroupMembersList();
      });
      selectedMembersChips.appendChild(chip);
    });
  }

  const filterQuery = (groupMemberSearchInput ? groupMemberSearchInput.value : '').trim().toLowerCase();
  groupMembersChecklist.innerHTML = '';

  const filteredUsers = onlineUsers.filter((u) => u.username.toLowerCase().includes(filterQuery));

  if (filteredUsers.length === 0) {
    groupMembersChecklist.innerHTML = '<div style="padding:12px; text-align:center; color:var(--text-muted); font-size:0.85rem;">No members match search query</div>';
    return;
  }

  filteredUsers.forEach((u) => {
    const isChecked = selectedGroupMemberSet.has(u.username);
    const item = document.createElement('div');
    item.className = 'group-member-item';
    const initial = u.username.charAt(0).toUpperCase();
    const moodText = u.mood_status || 'Available';

    item.innerHTML = `
      <div class="member-avatar">${initial}</div>
      <div class="member-info">
        <div class="member-name">${escapeHtml(u.username)}</div>
        <div class="member-mood">${escapeHtml(moodText)}</div>
      </div>
      <input type="checkbox" ${isChecked ? 'checked' : ''}>
    `;

    const cb = item.querySelector('input[type="checkbox"]');
    
    item.addEventListener('click', (e) => {
      if (e.target !== cb) {
        cb.checked = !cb.checked;
      }
      if (cb.checked) {
        selectedGroupMemberSet.add(u.username);
      } else {
        selectedGroupMemberSet.delete(u.username);
      }
      renderGroupMembersList();
    });

    groupMembersChecklist.appendChild(item);
  });
}

function openGroupModalWithPreselect(preselectUsername = null) {
  if (!createGroupModal) return;
  if (groupModalTitle) groupModalTitle.textContent = 'Create New Group';
  if (btnSaveGroup) btnSaveGroup.textContent = 'Create Group';
  editingGroupOriginalName = null;
  groupNameInput.value = '';
  if (groupMemberSearchInput) groupMemberSearchInput.value = '';

  selectedGroupMemberSet.clear();
  if (myUsername) selectedGroupMemberSet.add(myUsername);
  if (preselectUsername) selectedGroupMemberSet.add(preselectUsername);

  renderGroupMembersList();
  createGroupModal.classList.remove('hidden');
}

function openGroupModalForEdit(groupObj) {
  if (!createGroupModal) return;
  if (groupModalTitle) groupModalTitle.textContent = `Edit Group (${groupObj.group_name})`;
  if (btnSaveGroup) btnSaveGroup.textContent = 'Save Changes';
  editingGroupOriginalName = groupObj.group_name;
  groupNameInput.value = groupObj.group_name;
  if (groupMemberSearchInput) groupMemberSearchInput.value = '';

  selectedGroupMemberSet.clear();
  if (groupObj.members && Array.isArray(groupObj.members)) {
    groupObj.members.forEach((m) => selectedGroupMemberSet.add(m));
  }

  renderGroupMembersList();
  createGroupModal.classList.remove('hidden');
}

if (groupMemberSearchInput) {
  groupMemberSearchInput.addEventListener('input', renderGroupMembersList);
}

if (btnOpenCreateGroup) btnOpenCreateGroup.addEventListener('click', () => { openGroupModalWithPreselect(); });
if (btnCancelGroupModal) btnCancelGroupModal.addEventListener('click', () => { createGroupModal.classList.add('hidden'); });

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    if (createGroupModal && !createGroupModal.classList.contains('hidden')) {
      createGroupModal.classList.add('hidden');
    }
  }
});

if (btnSaveGroup) {
  btnSaveGroup.addEventListener('click', () => {
    const groupName = groupNameInput.value.trim();
    const selectedMembers = Array.from(selectedGroupMemberSet);
    
    if (!groupName) {
      showToast('Please enter a group name.', 'error');
      return;
    }

    if (myUsername && !selectedMembers.includes(myUsername)) {
      selectedMembers.push(myUsername);
    }

    if (editingGroupOriginalName) {
      if (editingGroupOriginalName !== groupName) {
        socket.emit('rename_broadcast_group', { old_name: editingGroupOriginalName, new_name: groupName });
      }
      socket.emit('update_group_members', { group_name: groupName, members: selectedMembers });
    } else {
      socket.emit('create_broadcast_group', { group_name: groupName, sender: myUsername, members: selectedMembers });
    }

    createGroupModal.classList.add('hidden');
    groupNameInput.value = '';
    editingGroupOriginalName = null;
  });
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/[&<>"']/g, function (m) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
  });
}
