const chatWindow = document.getElementById("chatWindow");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");
const statusBadge = document.getElementById("statusBadge");
const menuItems = document.querySelectorAll(".menu-item");
const topbarTitle = document.querySelector(".topbar h2");
const topbarSubtitle = document.querySelector(".topbar p");

let chatContentCache = chatWindow.innerHTML;

function setStatus(text, type = "ready") {
    statusBadge.textContent = text;
    statusBadge.className = "status-badge";

    if (type === "loading") {
        statusBadge.classList.add("loading");
    }

    if (type === "error") {
        statusBadge.classList.add("error");
    }
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function saveChatContent() {
    chatContentCache = chatWindow.innerHTML;
}

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function removeWelcomeCard() {
    const welcome = document.querySelector(".welcome-card");
    if (welcome) {
        welcome.remove();
    }
}

function addMessage(role, content) {
    removeWelcomeCard();

    const row = document.createElement("div");
    row.className = `message-row ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = escapeHtml(content);

    row.appendChild(bubble);
    chatWindow.appendChild(row);

    saveChatContent();
    scrollToBottom();
}

function addToolCard(step) {
    const card = document.createElement("div");
    card.className = "tool-card";

    const argsText = JSON.stringify(step.args || {}, null, 2);
    const resultText = step.result || "";

    card.innerHTML = `
        <div class="tool-header">
            <span>工具调用：<span class="tool-name">${escapeHtml(step.tool)}</span></span>
            <span>已完成</span>
        </div>
        <div class="tool-result">参数：
${escapeHtml(argsText)}

结果：
${escapeHtml(resultText)}</div>
    `;

    chatWindow.appendChild(card);

    saveChatContent();
    scrollToBottom();
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessage("user", message);
    messageInput.value = "";

    sendBtn.disabled = true;
    setStatus("妲己思索中...", "loading");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `请求失败：${response.status}`);
        }

        const data = await response.json();

        if (data.steps && data.steps.length > 0) {
            data.steps.forEach(addToolCard);
        }

        addMessage("agent", data.reply || "妾身没有得到有效回复。");
        setStatus("已就绪");

    } catch (error) {
        addMessage("agent", `出错了：${error.message}`);
        setStatus("出错", "error");

    } finally {
        sendBtn.disabled = false;
        messageInput.focus();
    }
}

async function clearMemory() {
    const ok = confirm("确定要清空当前聊天记忆吗？");

    if (!ok) {
        return;
    }

    try {
        const response = await fetch("/clear", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error(`清空失败：${response.status}`);
        }

        await response.json();

        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">记忆已清空。</div>
                <p>妲己已重新候命，主人可以重新吩咐。</p>
            </div>
        `;
        saveChatContent();
        setStatus("记忆已清空");

    } catch (error) {
        alert(error.message);
        setStatus("出错", "error");
    }
}

async function loadChatHistory() {
    try {
        const response = await fetch("/history");

        if (!response.ok) {
            throw new Error(`读取聊天记录失败：${response.status}`);
        }

        const data = await response.json();

        if (!data.history || data.history.length === 0) {
            saveChatContent();
            return;
        }

        removeWelcomeCard();

        data.history.forEach((record) => {
            addMessage("user", record.user || "");

            if (record.steps && record.steps.length > 0) {
                record.steps.forEach(addToolCard);
            }

            addMessage("agent", record.reply || "");
        });

        saveChatContent();
        setStatus(`已恢复 ${data.count} 条记录`);

    } catch (error) {
        console.warn("聊天记录恢复失败：", error);
        setStatus("历史恢复失败", "error");
    }
}

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = `${messageInput.scrollHeight}px`;
});

clearBtn.addEventListener("click", clearMemory);

function setActiveMenu(page) {
    menuItems.forEach((item) => {
        if (item.dataset.page === page) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });
}

function showChatPage() {
    setActiveMenu("chat");
    topbarTitle.textContent = "御前对话";
    topbarSubtitle.textContent = "Daji Agent · Tool Calling Runtime";

    chatWindow.innerHTML = chatContentCache;
    scrollToBottom();
    

    messageInput.disabled = false;
    sendBtn.disabled = false;
    messageInput.placeholder = "主人有何吩咐？例如：帮我查看当前 Python 版本";
}

async function showToolsPage() {
    setActiveMenu("tools");
    topbarTitle.textContent = "工具札记";
    topbarSubtitle.textContent = "Daji Agent · Registered Tools";

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = "工具札记页面暂不支持输入";

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">正在取来工具札记……</div>
            <p>妲己正在查看当前已注册的工具。</p>
        </div>
    `;

    try {
        const response = await fetch("/tools");

        if (!response.ok) {
            throw new Error(`获取工具列表失败：${response.status}`);
        }

        const data = await response.json();

        const cards = data.tools.map((tool) => {
            const params = tool.parameters?.properties || {};
            const paramNames = Object.keys(params);

            const paramsHtml = paramNames.length
                ? paramNames.map((name) => {
                    const desc = params[name]?.description || "";
                    return `<li><strong>${escapeHtml(name)}</strong>：${escapeHtml(desc)}</li>`;
                }).join("")
                : "<li>无参数</li>";

            return `
                <div class="tool-page-card">
                    <div class="tool-page-title">${escapeHtml(tool.name)}</div>
                    <p>${escapeHtml(tool.description)}</p>
                    <div class="tool-page-subtitle">参数</div>
                    <ul>${paramsHtml}</ul>
                </div>
            `;
        }).join("");

        chatWindow.innerHTML = `
            <div class="page-panel">
                <h3>妲己当前可用工具</h3>
                <p class="page-desc">当前共注册 ${data.count} 个工具。工具由后端 Python 真正执行，模型只负责判断何时调用。</p>
                <div class="tool-page-grid">
                    ${cards}
                </div>
            </div>
        `;

        setStatus("工具已载入");

    } catch (error) {
        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">工具札记读取失败。</div>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        setStatus("出错", "error");
    }
}
async function showSkillsPage() {
    setActiveMenu("skills");
    topbarTitle.textContent = "Skills";
    topbarSubtitle.textContent = "Daji Agent · Skill Packages";

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = "Skills 页面暂不支持输入";

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">正在取来技能卷宗……</div>
            <p>妲己正在查看当前已安装的技能包。</p>
        </div>
    `;

    try {
        const response = await fetch("/skills");

        if (!response.ok) {
            throw new Error(`获取技能包失败：${response.status}`);
        }

        const data = await response.json();

        const cards = data.skills.map((skill) => {
            return `
                <div class="skill-page-card">
                    <div class="skill-page-title">${escapeHtml(skill.title)}</div>
                    <p>${escapeHtml(skill.description)}</p>
                    <div class="skill-page-path">${escapeHtml(skill.path)}</div>
                    <div class="skill-page-name">调用名：${escapeHtml(skill.name)}</div>
                </div>
            `;
        }).join("");

        chatWindow.innerHTML = `
            <div class="page-panel">
                <h3>妲己当前技能包</h3>
                <p class="page-desc">
                    当前共安装 ${data.count} 个技能包。技能包不是工具本身，而是妲己做某类任务前会读取的“方法说明书”。
                </p>
                <div class="tool-page-grid">
                    ${cards}
                </div>
            </div>
        `;

        setStatus("技能已载入");

    } catch (error) {
        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">技能卷宗读取失败。</div>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        setStatus("出错", "error");
    }
}

async function showMemoryPage() {
    setActiveMenu("memory");
    topbarTitle.textContent = "Memory";
    topbarSubtitle.textContent = "Daji Agent · Long-term Memory";

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = "Memory 页面暂不支持输入";

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">正在翻阅记忆卷宗……</div>
            <p>妲己正在查看本地长期记忆。</p>
        </div>
    `;

    try {
        const response = await fetch("/memory");

        if (!response.ok) {
            throw new Error(`获取长期记忆失败：${response.status}`);
        }

        const data = await response.json();

        const cards = data.memories.length
            ? data.memories.map((memory) => {
                return `
                    <div class="memory-page-card">
                        <div class="memory-page-title">${escapeHtml(memory.category || "general")}</div>
                        <p>${escapeHtml(memory.content || "")}</p>
                        <div class="memory-page-meta">
                            id: ${escapeHtml(memory.id || "")}
                            · ${escapeHtml(memory.created_at || "")}
                        </div>
                    </div>
                `;
            }).join("")
            : `
                <div class="welcome-card">
                    <div class="welcome-title">暂无长期记忆。</div>
                    <p>主人可以在对话中说：“请记住：我喜欢你用中文、分步骤解释。”</p>
                </div>
            `;

        chatWindow.innerHTML = `
            <div class="page-panel">
                <h3>妲己长期记忆</h3>
                <p class="page-desc">
                    当前共保存 ${data.count} 条长期记忆。这些内容保存在本地 data/memory.json，
                    关闭程序后仍会保留。
                </p>
                <div class="memory-actions">
                    <button id="clearLongMemoryBtn">清空长期记忆</button>
                </div>
                <div class="tool-page-grid">
                    ${cards}
                </div>
            </div>
        `;

        const clearLongMemoryBtn = document.getElementById("clearLongMemoryBtn");

        clearLongMemoryBtn.addEventListener("click", clearLongTermMemory);

        setStatus("记忆已载入");

    } catch (error) {
        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">记忆卷宗读取失败。</div>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        setStatus("出错", "error");
    }
}

async function showTodosPage() {
    setActiveMenu("todos");
    topbarTitle.textContent = "Todo";
    topbarSubtitle.textContent = "Daji Agent · Task Planning";

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = "Todo 页面暂不支持输入";

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">正在展开任务卷轴……</div>
            <p>妲己正在查看当前任务计划。</p>
        </div>
    `;

    try {
        const response = await fetch("/todos");

        if (!response.ok) {
            throw new Error(`获取 Todo 失败：${response.status}`);
        }

        const data = await response.json();

        const cards = data.todos.length
            ? data.todos.map((todo) => {
                return `
                    <div class="todo-page-card">
                        <div class="todo-page-top">
                            <span class="todo-order">#${escapeHtml(todo.order || "")}</span>
                            <span class="todo-status ${escapeHtml(todo.status || "pending")}">
                                ${escapeHtml(todo.status || "pending")}
                            </span>
                        </div>
                        <p>${escapeHtml(todo.content || "")}</p>
                        <div class="todo-meta">
                            id: ${escapeHtml(todo.id || "")}
                            · ${escapeHtml(todo.updated_at || "")}
                        </div>
                    </div>
                `;
            }).join("")
            : `
                <div class="welcome-card">
                    <div class="welcome-title">暂无 Todo。</div>
                    <p>主人可以回到聊天页说：“请帮我制定一个完善 Agent 项目的计划。”</p>
                </div>
            `;

        chatWindow.innerHTML = `
            <div class="page-panel">
                <h3>任务规划 Todo</h3>
                <p class="page-desc">
                    当前共有 ${data.count} 个任务。Todo 用来帮助妲己在复杂任务中先规划、再执行。
                </p>
                <div class="memory-actions">
                    <button id="clearTodosBtn">清空 Todo</button>
                </div>
                <div class="tool-page-grid">
                    ${cards}
                </div>
            </div>
        `;

        const clearTodosBtn = document.getElementById("clearTodosBtn");
        clearTodosBtn.addEventListener("click", clearTodos);

        setStatus("Todo 已载入");

    } catch (error) {
        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">Todo 读取失败。</div>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        setStatus("出错", "error");
    }
}


async function clearTodos() {
    const ok = confirm("确定要清空 Todo 列表吗？");

    if (!ok) {
        return;
    }

    try {
        const response = await fetch("/todos/clear", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error(`清空 Todo 失败：${response.status}`);
        }

        await response.json();

        showTodosPage();
        setStatus("Todo 已清空");

    } catch (error) {
        alert(error.message);
        setStatus("出错", "error");
    }
}

async function showSettingsPage() {
    setActiveMenu("settings");
    topbarTitle.textContent = "Settings";
    topbarSubtitle.textContent = "Daji Agent · Runtime Settings";

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = "Settings 页面暂不支持输入";

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">正在查看运行配置……</div>
            <p>妲己正在读取当前后端状态。</p>
        </div>
    `;

    try {
        const response = await fetch("/status");

        if (!response.ok) {
            throw new Error(`获取运行状态失败：${response.status}`);
        }

        const data = await response.json();

        chatWindow.innerHTML = `
            <div class="page-panel">
                <h3>运行设置</h3>
                <p class="page-desc">
                    这里展示 Daji Agent Studio 当前的后端状态、模型配置和资源数量。
                    注意：页面不会显示 API Key。
                </p>

                <div class="settings-grid">
                    <div class="settings-card">
                        <div class="settings-label">项目名称</div>
                        <div class="settings-value">${escapeHtml(data.project)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">版本</div>
                        <div class="settings-value">${escapeHtml(data.version)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">当前模型</div>
                        <div class="settings-value">${escapeHtml(data.model)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">接口地址</div>
                        <div class="settings-value">${escapeHtml(data.base_url)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">工具数量</div>
                        <div class="settings-value">${escapeHtml(data.tools_count)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">技能包数量</div>
                        <div class="settings-value">${escapeHtml(data.skills_count)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">长期记忆数量</div>
                        <div class="settings-value">${escapeHtml(data.memory_count)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">Todo 数量</div>
                        <div class="settings-value">${escapeHtml(data.todo_count)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">后端状态</div>
                        <div class="settings-value">${escapeHtml(data.backend)}</div>
                    </div>

                    <div class="settings-card">
                        <div class="settings-label">API Key 状态</div>
                        <div class="settings-value">${data.api_key_loaded ? "已加载" : "未加载"}</div>
                    </div>

                    
                </div>
            </div>
        `;

        setStatus("设置已载入");

    } catch (error) {
        chatWindow.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-title">设置读取失败。</div>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;

        setStatus("出错", "error");
    }
}

async function clearLongTermMemory() {
    const ok = confirm("确定要清空长期记忆吗？这会删除 data/memory.json 中保存的记忆。");

    if (!ok) {
        return;
    }

    try {
        const response = await fetch("/memory/clear", {
            method: "POST"
        });

        if (!response.ok) {
            throw new Error(`清空长期记忆失败：${response.status}`);
        }

        await response.json();

        showMemoryPage();
        setStatus("长期记忆已清空");

    } catch (error) {
        alert(error.message);
        setStatus("出错", "error");
    }
}

function showComingSoonPage(pageName, title, subtitle) {
    setActiveMenu(pageName);
    topbarTitle.textContent = title;
    topbarSubtitle.textContent = subtitle;

    messageInput.disabled = true;
    sendBtn.disabled = true;
    messageInput.placeholder = `${title} 页面后续开发`;

    chatWindow.innerHTML = `
        <div class="welcome-card">
            <div class="welcome-title">${title}，尚在修筑中。</div>
            <p>
                这一页后续会继续实现。当前我们先完成 Chat、Tools，
                再逐步加入 Skills、Memory 和 Settings。
            </p>
        </div>
    `;
}

menuItems.forEach((item) => {
    item.addEventListener("click", () => {
        const page = item.dataset.page;

        if (page === "chat") {
            showChatPage();
        } else if (page === "tools") {
            showToolsPage();
        } else if (page === "skills") {
            showSkillsPage();
        } else if (page === "skills") {
            showComingSoonPage("skills", "Skills", "Daji Agent · Skill Packages");
        } else if (page === "memory") {
            showMemoryPage();
        } else if (page === "todos") {
            showTodosPage();
        } else if (page === "settings") {
            showSettingsPage();
        }

    });
});

// 页面加载时自动恢复聊天记录
loadChatHistory();