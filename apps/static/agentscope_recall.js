const promptInput = document.getElementById("promptInput");
const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const statusText = document.getElementById("statusText");
const eventTimeline = document.getElementById("eventTimeline");

let source = null;
const timelineEntries = new Map();

function setStatus(text) {
  statusText.textContent = text;
}

function resetView() {
  eventTimeline.innerHTML = "";
  timelineEntries.clear();
}

function formatPayload(payload) {
  if (typeof payload === "string") {
    return payload;
  }
  return JSON.stringify(payload, null, 2);
}

function createTimelineEntry(kind, label) {
  const item = document.createElement("div");
  item.className = `timeline-item ${kind}`;

  const titleNode = document.createElement("div");
  titleNode.className = "title";

  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = label;

  const content = document.createElement("pre");
  content.textContent = "";

  titleNode.appendChild(badge);
  item.appendChild(titleNode);
  item.appendChild(content);
  eventTimeline.appendChild(item);

  return { item, content };
}

function ensureTimelineEntry(key, kind, label) {
  if (!timelineEntries.has(key)) {
    timelineEntries.set(key, createTimelineEntry(kind, label));
  }
  return timelineEntries.get(key);
}

function stopStream(reason = "已停止") {
  if (source) {
    source.close();
    source = null;
  }
  sendBtn.disabled = false;
  stopBtn.disabled = true;
  setStatus(reason);
}

function startStream(prompt) {
  stopStream("准备中...");
  resetView();
  sendBtn.disabled = true;
  stopBtn.disabled = false;
  setStatus("流式处理中...");

  const url = `/api/chat/stream?prompt=${encodeURIComponent(prompt)}`;
  source = new EventSource(url);

  source.addEventListener("text_delta", (event) => {
    const data = JSON.parse(event.data);
    const key = `text:${data.message_id}`;
    const entry = ensureTimelineEntry(key, "text", "TEXT");
    entry.content.textContent += data.delta || "";
  });

  source.addEventListener("thinking_delta", (event) => {
    const data = JSON.parse(event.data);
    const key = `thinking:${data.message_id}`;
    const entry = ensureTimelineEntry(key, "thinking", "THINKING");
    entry.content.textContent += data.delta || "";
  });

  source.addEventListener("tool_use", (event) => {
    const data = JSON.parse(event.data);
    const uniqueId = `tool_use:${data.tool_call_id || data.message_id || crypto.randomUUID()}`;
    if (timelineEntries.has(uniqueId)) {
      return;
    }
    const entry = ensureTimelineEntry(uniqueId, "tool_use", `TOOL USE · ${data.tool_name || "unknown"}`);
    entry.content.textContent = formatPayload(data.arguments || {});
  });

  source.addEventListener("tool_result", (event) => {
    const data = JSON.parse(event.data);
    const uniqueId = `tool_result:${data.tool_call_id || data.message_id || crypto.randomUUID()}`;
    if (timelineEntries.has(uniqueId)) {
      return;
    }
    const entry = ensureTimelineEntry(uniqueId, "tool_result", `TOOL RESULT · ${data.tool_name || "unknown"}`);
    entry.content.textContent = formatPayload(data.output);
  });

  source.addEventListener("done", () => {
    stopStream("完成");
  });

  source.addEventListener("error", (event) => {
    try {
      const data = JSON.parse(event.data);
      setStatus(`错误: ${data.message || "unknown error"}`);
    } catch (_err) {
      setStatus("连接错误或后端中断");
    }
    stopStream(statusText.textContent);
  });

  source.onerror = () => {
    if (source) {
      stopStream("连接已关闭");
    }
  };
}

sendBtn.addEventListener("click", () => {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("请输入问题后再发送");
    return;
  }
  startStream(prompt);
});

stopBtn.addEventListener("click", () => {
  stopStream("用户停止");
});
