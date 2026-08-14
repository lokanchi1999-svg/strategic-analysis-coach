"use client";

import { FormEvent, useState } from "react";
import { API_BASE_URL, backendNetworkErrorMessage } from "../lib/config";

type Session = {
  session_id: string;
  mode: string;
  phase: string;
  active_skill?: string;
  current_dimension?: string;
  current_depth: number;
  turn_count: number;
  last_evaluation?: Record<string, unknown> | null;
  last_question_action?: string | null;
  framework_selection: { status: string };
  messages: { role: string; content: string }[];
};

class ApiError extends Error {
  constructor(message: string, public errorType?: string, public stage?: string) { super(message); }
}
async function readJson(response: Response) {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(body.message || body.detail || `后端请求失败（HTTP ${response.status}）`, body.error_type, body.stage);
  return body;
}

export default function Home() {
  const showDebugPanel = process.env.NODE_ENV === "development";
  const [adapter, setAdapter] = useState("mock");
  const [key, setKey] = useState("");
  const [base, setBase] = useState("https://api.openai.com/v1");
  const [model, setModel] = useState("mock-model");
  const [status, setStatus] = useState("");
  const [mode, setMode] = useState("guided");
  const [input, setInput] = useState("SAMPLE-CASE-01");
  const [session, setSession] = useState<Session | null>(null);
  const [message, setMessage] = useState("");

  const profile = {
    adapter,
    base_url: base,
    structured_output_mode: "auto",
    models: { default: model },
    generation: { temperature: 0.2, max_output_tokens: 1500, timeout_seconds: 60 },
  };

  function showRequestError(error: unknown, operation: string) {
    if (error instanceof TypeError) setStatus(backendNetworkErrorMessage());
    else if (error instanceof ApiError && error.errorType === "MODEL_TIMEOUT") setStatus("模型响应超时。当前 Session 状态未推进，请重试或适当调整 timeout。")
    else if (error instanceof ApiError && ["INVALID_STRUCTURED_OUTPUT", "STRUCTURED_OUTPUT_REPAIR_FAILED"].includes(error.errorType || "")) setStatus("模型评估失败：返回内容不符合 Evaluator 结构要求。系统未推进当前分析状态，请重试或更换模型。")
    else if (error instanceof ApiError && error.errorType === "MODEL_RATE_LIMITED") setStatus("模型服务当前限流。Session 状态未推进，请稍后重试。")
    else if (error instanceof ApiError && error.errorType === "MODEL_AUTHENTICATION_FAILED") setStatus("模型认证失败，请检查 API Key。Session 状态未推进。")
    else if (error instanceof ApiError && error.stage === "question_generator") setStatus("问题生成失败。系统未提交分析状态，请重试。")
    else setStatus(`${operation}失败：${error instanceof Error ? error.message : "未知错误"}`);
  }

  async function testConnection() {
    setStatus("测试中…");
    try {
      const response = await fetch(`${API_BASE_URL}/api/model/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, credentials: { api_key: key || null } }),
      });
      const body = await readJson(response);
      const checks = body.checks ? `（基础生成：${body.checks.basic_completion ? "通过" : "失败"}；Evaluator：${body.checks.evaluation_schema ? "通过" : "失败"}）` : "";
      setStatus(body.success ? `✓ ${body.message}${checks}` : `✗ ${body.error_type}: ${body.message}${checks}`);
    } catch (error) {
      showRequestError(error, "连接测试");
    }
  }

  async function startSession() {
    const body = mode === "guided"
      ? { mode, case_code: input, model_profile: profile, credentials: { api_key: key || null } }
      : { mode, material: input, model_profile: profile, credentials: { api_key: key || null } };
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setSession(await readJson(response));
      setStatus("");
    } catch (error) {
      showRequestError(error, "创建 Session");
    }
  }

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    if (!session || !message.trim()) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions/${session.session_id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: message }),
      });
      const body = await readJson(response);
      setSession(body.session);
      setMessage("");
      setStatus("");
    } catch (error) {
      showRequestError(error, "发送消息");
    }
  }

  return <main>
    <header><span className="eyebrow">v0.2 Content-ready Architecture</span><h1>Strategic Analysis Coach</h1><p>用追问训练战略推理，而不是替你交出答案。</p></header>
    <div className="grid">
      <section><h2>1 · Model Settings</h2>
        <label>Adapter<select value={adapter} onChange={event => { setAdapter(event.target.value); if (event.target.value === "mock") setModel("mock-model"); }}><option value="mock">Mock（无需 Key）</option><option value="openai_compatible">OpenAI-compatible</option></select></label>
        <label>API Key<input type="password" value={key} onChange={event => setKey(event.target.value)} autoComplete="off" /></label>
        <label>Base URL<input value={base} onChange={event => setBase(event.target.value)} /></label>
        <label>Default Model<input value={model} onChange={event => setModel(event.target.value)} /></label>
        <button className="secondary" onClick={testConnection}>Test Connection</button>{status && <p className="status">{status}</p>}
      </section>
      <section><h2>2 · Start Session</h2><div className="toggle"><button className={mode === "guided" ? "active" : ""} onClick={() => { setMode("guided"); setInput("SAMPLE-CASE-01"); }}>Guided Case</button><button className={mode === "free" ? "active" : ""} onClick={() => { setMode("free"); setInput(""); }}>Free Analysis</button></div>
        <label>{mode === "guided" ? "Case Code" : "Material / Case Description"}{mode === "guided" ? <input value={input} onChange={event => setInput(event.target.value)} /> : <textarea rows={7} value={input} onChange={event => setInput(event.target.value)} />}</label>
        <button onClick={startSession}>创建 Session</button>
      </section>
    </div>
    {session && <section className="chat"><div className="meta"><span>Mode <b>{session.mode}</b></span><span>Phase <b>{session.phase}</b></span><span>Framework <b>{session.active_skill || "待选择"}</b></span><span>Dimension <b>{session.current_dimension || "—"}</b></span></div>
      <div className="messages">{session.messages.length === 0 ? <p className="empty">Session 已建立，写下你的第一个判断。</p> : session.messages.map((item, index) => <div key={index} className={`bubble ${item.role}`}><small>{item.role === "coach" ? "Coach" : "You"}</small>{item.content}</div>)}</div>
      <form onSubmit={sendMessage}><textarea value={message} onChange={event => setMessage(event.target.value)} placeholder="写下你的判断、证据或框架选择…" /><button>发送</button></form>
    </section>}
    {showDebugPanel && session && <aside className="debug-panel">
      <h2>Developer Debug</h2>
      <dl>
        <dt>Session ID</dt><dd>{session.session_id}</dd><dt>Mode</dt><dd>{session.mode}</dd>
        <dt>Phase</dt><dd>{session.phase}</dd><dt>Active Skill</dt><dd>{session.active_skill || "—"}</dd>
        <dt>Current Dimension</dt><dd>{session.current_dimension || "—"}</dd><dt>Current Depth</dt><dd>{session.current_depth}</dd>
        <dt>Turn Count</dt><dd>{session.turn_count}</dd><dt>Last Question Action</dt><dd>{session.last_question_action || "—"}</dd>
        <dt>Framework Selection</dt><dd>{session.framework_selection.status}</dd>
      </dl>
      {session.last_evaluation && <details><summary>Show evaluation JSON</summary><pre>{JSON.stringify(session.last_evaluation, null, 2)}</pre></details>}
    </aside>}
  </main>;
}
