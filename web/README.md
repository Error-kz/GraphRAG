## web 模块说明（前端）

`web` 目录存放的是**前端静态页面**，是一个通用的单页聊天界面 `index.html`。

- **路径**：`web/index.html`
- **主要功能**
  - 提供“AI 知识问答助手”的对话界面（领域无关）；
  - 展示用户和机器人对话气泡；
  - 展示多源检索路径（向量检索 / 知识图谱查询）的可视化信息；
  - 展示最终回答以及知识图谱查询置信度等。

- **与后端的交互方式**
  - 在页面底部的 `<script>` 中定义：
    - `const API_URL = window.location.origin + '/';`
  - 当用户点击“发送”或按回车时：
    - 使用 `fetch(API_URL, { method: 'POST', body: JSON.stringify({ question }) })`；
    - 即向当前域名的根路径 `POST /` 发送问题；
    - 对应后端 `services/agent_service.py` 中的 `@app.post("/")` 接口。
  - 页面展示：
    - `search_stages`：每个检索阶段的状态（成功 / 失败 / 无结果）与部分结果摘要；
    - `search_path`：实际使用到的检索链路；
    - `response`：最终回答内容。

> 启动方式：通过 `start.sh` 启动 Agent 服务后，浏览器访问 `http://localhost:8103/` 即可加载此页面。

---