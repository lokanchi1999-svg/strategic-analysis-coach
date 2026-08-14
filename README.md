# Strategic Analysis Coach v0.2

面向商学院/战略管理课程的交互式教学 Agent。v0.2 是 content-ready architecture：核心契约、内容验证、独立 Eval Harness 与安全的开发调试面板已经就位，教师材料仍保持 placeholder。

## 快速启动

要求 Python 3.12+、Node.js 20+。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

打开 `http://localhost:3000`；API 文档为 `http://localhost:8000/docs`。也可在项目根目录执行：

```bash
docker compose up --build
```

## Local Development Networking

本机开发默认使用 Frontend `http://localhost:3000` 和 Backend `http://localhost:8000`，无需创建 `.env.local`；`http://127.0.0.1:3000` 也被明确允许。前端统一从 `frontend/lib/config.ts` 读取 `NEXT_PUBLIC_API_URL`，没有设置时回退到 `http://localhost:8000`。

若要自定义 Backend URL，将 `frontend/.env.local.example` 复制为 `frontend/.env.local` 后修改，例如：

```text
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

`config/app.yaml` 的 development CORS 会额外允许端口 `3000` 上的 RFC1918 私有 IPv4 Origin：`10.0.0.0/8`、`172.16.0.0/12` 和 `192.168.0.0/16`。它不会允许公网 Origin、HTTPS、其他端口或范围外地址。生产配置应使用 `environment: production`、将 `allow_local_network_origins` 设为 `false`，并只在 `allowed_origins` 中列出实际部署域名。

如果只是从本机浏览器通过 Next.js 显示的 Network URL `http://<LAN-IP>:3000` 打开页面，development CORS 已允许该 Origin。如果从另一台设备访问，Backend 也必须监听局域网接口：

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

同时把前端配置设为运行 Backend 的电脑地址：

```text
NEXT_PUBLIC_API_URL=http://<HOST-LAN-IP>:8000
```

另一台设备上的 `localhost` 指那台设备自身，并不指运行 Backend 的电脑。修改 `.env.local` 后需要重新启动 Next.js。

默认界面选择 `Mock`，无需 API Key。使用兼容接口时，选择 `OpenAI-compatible`，填写 Base URL、模型和 Key，再点击 Test Connection。Key 仅进入后端进程内的 SessionCredentialVault，删除 Session 时清除；不写入 Session、日志、案例或磁盘。

### Real Model Compatibility

`Test Connection` 现在会使用纯 synthetic input 检查 Provider 可达性、认证、基础 completion、结构化 JSON 和 `EvaluationResult` schema，不加载 Case 或教师隐藏内容。

`ModelProfile.structured_output_mode` 向后兼容，默认 `auto`：依次尝试 `json_schema`、`json_object`、`prompt_only`。只有 Provider 明确返回 400/422 拒绝当前格式时才降级；认证、timeout 和限流不会被误判为 capability 不支持。所有模式最终仍由严格 Pydantic contract 验证。

Evaluator 使用独立 internal-only prompt，完整 schema 和最小结构示例随请求发送。第一次输出不符合 schema 时允许一次只修结构的 repair；第二次仍失败则返回 `STRUCTURED_OUTPUT_REPAIR_FAILED`。HTTP Read/Connect timeout、临时 429 和 5xx 最多传输重试一次，结构 repair 与传输 retry 相互独立。

受控模型错误响应包含安全的 `error_type`、`stage` 和 `message`，合法 Origin 的错误响应仍保留 CORS header。前端分别提示 timeout、结构错误、限流、认证和 Question Generator 失败，不显示 traceback、Key 或内部上下文。

## 架构边界

- `backend/core/`：Controller、Context Builder、Evaluator、状态迁移、Question Generator、Orchestrator。
- `backend/model_gateway/`：统一 `ModelGateway.generate()` 契约，含 Mock 与 OpenAI-compatible adapter。
- `backend/storage/`：内存 Session、文件 Skill/Case repository；可替换为 Redis/PostgreSQL。
- `coach_core/`：跨 Skill 的核心政策、状态机和问题动作。
- `skills/`：Meta Skill 与 Analysis Skill；不包含具体案例。
- `cases/`：公开学生材料和服务端教师标注；API 只返回专用 `PublicCase`。
- `instructors/`：教师 profile 与 rubric override 预留层。
- `frontend/`：Model Settings、Session 创建和 Chat 三个区域。

主循环是：学生消息 → Evaluator（严格 Pydantic）→ State Transition → Question Generator → 学生可见回复。Session State 与聊天历史分离，API route 不直接修改状态字段。

## 扩展方式

新增 Analysis Skill：建立 `skills/analysis/vrio/`，至少包含 `manifest.yaml`、`ontology.yaml`、`rubric.yaml`、`questioning_policy.yaml`、`tests/`。loader 自动发现，无需修改核心 Engine。

新增 Case：建立 `cases/CASE-XXX-01/`，目录名与 manifest 的 `case_code` 必须精确一致；添加 `manifest.yaml`、`student_material.md` 和 `teacher_annotations.yaml`。

新增 Provider：实现 `backend/model_gateway/base.py` 中的 `ModelGateway`，将 provider 响应归一化为 `GatewayResponse`，再在 `registry.py` 注册。不要在 Skill 中写模型名或 Key。

## 当前 Placeholder / 教师材料填充位置

- `coach_core/core_policy.md`、`state_machine.yaml`、`question_actions.yaml`：核心追问引擎与状态策略。
- `skills/analysis/five_forces/rubric.yaml`：深度分级标准。
- 同目录 `ontology.yaml`、`misconceptions.yaml`、`questioning_policy.yaml`、`examples.json`：框架知识与教学策略。
- `skills/meta/framework_selection/`：框架目录、判别规则与标注示例。
- `cases/*/teacher_annotations.yaml`：具体案例的教师判断与事实标签。
- `instructors/*/rubric_overrides/`：教师覆盖规则。

当前 Framework Selection 和 Mock 追问只做演示性 placeholder，不代表最终教学逻辑；SWOT 目前仅有候选元数据，未安装 Analysis Skill。

## Content Authoring

建议按以下边界导入教师材料：

1. `coach_core/`：跨框架的核心教学政策、状态机和 QuestionAction 映射。
2. `skills/analysis/<skill_id>/`：某一分析框架的 manifest、ontology、rubric、questioning policy，以及可选 misconceptions/examples。
3. `skills/meta/framework_selection/`：只保存框架元数据与选择规则，不加载完整 Analysis Skill 内容。
4. `cases/<CASE-CODE>/`：公开 `student_material.md` 与仅后端使用的 `teacher_annotations.yaml`。
5. `instructors/<instructor_id>/rubric_overrides/`：教师对基础 Skill 的覆盖规则。

Case 目录名必须和 `manifest.case_code` 完全一致。Skill 目录名必须和 `manifest.id` 一致。不要把案例判断写进 Skill，也不要把教师隐藏内容写进学生材料。

## Content Validation

从项目根目录运行：

```bash
python -m backend.tools.validate_skill skills/analysis/five_forces
python -m backend.tools.validate_case cases/SAMPLE-CASE-01
python -m backend.tools.validate_all
```

Validator 检查必需文件、严格 manifest、目录 ID、维度和 depth level 一致性、重复 item ID、Skill/Instructor 跨引用、非空学生材料和可解析教师 YAML。教师 TODO placeholder 会产生 warning，不会导致失败；结构或引用错误返回非零退出码，适合接入 CI。

## Teaching Evals

Eval Harness 独立于 pytest，dataset 使用统一 JSON contract：`id`、`category`、`input`、`expected`、`notes`。运行全部或单个 suite：

```bash
python -m backend.evals.run --adapter mock
python -m backend.evals.run --suite five_forces --adapter mock
python -m backend.evals.run --suite state_transition --json
```

当前指标包括 depth、advance、recommended action、framework selection 和 answer leakage skeleton。`evals/` 中所有现有数据均为 **DEVELOPMENT PLACEHOLDER — NOT INSTRUCTOR-VALIDATED**，仅验证加载、比较和报告链路，不构成教学 benchmark。

## Development Debug Panel

Debug Panel 只在 `next dev` 中显示，production build 会在编译期隐藏。它显示 Session ID、Mode、Phase、Active Skill、Dimension、Depth、Turn Count、上次 QuestionAction、Framework Selection 状态和可折叠的学生安全 Evaluation JSON。API Key、credentials、教师标注、内部 evaluation notes 和隐藏推理不属于其 payload。

## 测试

```bash
python -m pytest -q
```

覆盖冻结契约、递归公开响应防泄漏、Key/日志防泄漏、内容 validator、自动发现新 Skill/Case、Guided/Free 状态路径、状态迁移、Mock Evaluator、非法结构化输出、timeout 和 Question Generator 失败保护。

## Security

前端不展示 Key、教师标注或隐藏上下文。公开 API 使用 `PublicCase` / `PublicSessionView` 显式白名单；内部 Evaluation notes 不进入 public view。日志仅记录 request id、route、status、latency，不记录请求体和 Authorization。当前仍为单进程内存 Session，服务重启后状态与 Key 都消失。
