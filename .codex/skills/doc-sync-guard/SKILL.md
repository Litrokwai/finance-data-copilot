---
name: doc-sync-guard
description: 当修改 Finance Data Copilot 项目的代码、接口、数据库表结构、依赖、目录结构、技术栈、功能边界、配置、Docker、README 或 docs 文档时，必须触发本 Skill。用于强制检查并同步更新 README.md、PRD.md、Tech_Stack.md、Database_Design.md、AI_Coding_Rules.md、Project_Structure.md 等项目文档，防止代码和文档不一致。
---

# doc-sync-guard

## 目标

你是 Finance Data Copilot 项目的文档同步守卫。

每次对项目进行代码修改、功能调整、接口调整、数据库调整、依赖调整、目录结构调整、配置调整、部署方式调整时，必须检查相关文档是否需要同步更新。

核心目标：

1. 保证代码和文档一致。
2. 保证 README、PRD、技术栈、数据库设计、项目结构、AI 编码规则持续准确。
3. 防止项目开发过程中出现“代码已经变了，文档没有更新”的情况。
4. 每次修改完成后，必须明确说明本次更新了哪些文档，以及哪些文档不需要更新的原因。

---

## 项目背景

当前项目名称：

Finance Data Copilot

中文名：

金融数据 AI 开发助手

项目定位：

面向金融数据开发场景的 AI 数据开发助手，支持 SQL 解释、SQL 风险检查、数据字典管理、指标口径管理、RAG 问答、Text-to-SQL 原型和 SQL Agent 后续扩展能力。

当前已确定技术栈：

前端：

- React
- TypeScript
- Vite
- Ant Design
- React Router
- TanStack Query
- Axios
- Monaco Editor
- ECharts

后端：

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- SQLGlot

数据库：

- PostgreSQL
- pgvector

AI / RAG：

- 大模型 API
- Embedding API
- 轻量自研 RAG 流程
- 后期可考虑 LangGraph

部署：

- Docker
- Docker Compose

---

## 必须检查的文档清单

每次修改后，必须检查以下文件是否需要同步更新：

1. README.md
2. docs/PRD.md
3. docs/Tech_Stack.md
4. docs/Database_Design.md
5. docs/AI_Coding_Rules.md
6. docs/Project_Structure.md
7. docs/API_Design.md，如果项目中存在
8. docs/Changelog.md，如果项目中存在
9. database/schema.sql，如果涉及数据库结构
10. database/seed.sql，如果涉及初始化数据
11. .env.example，如果涉及环境变量
12. docker-compose.yml，如果涉及服务、端口、镜像、容器配置

如果某个文档不存在，但本次修改明显需要它，请创建对应文档，或者在最终说明中建议创建。

---

## 触发场景

遇到以下任意情况，必须触发本 Skill。

### 1. 功能变化

包括但不限于：

- 新增页面
- 删除页面
- 修改页面功能
- 新增后端接口
- 修改后端接口
- 删除后端接口
- 新增业务模块
- 修改业务流程
- 修改 V1 / V2 / V3 功能边界

需要重点检查：

- README.md
- docs/PRD.md
- docs/API_Design.md
- docs/Project_Structure.md

### 2. 技术栈变化

包括但不限于：

- 新增前端依赖
- 新增后端依赖
- 替换技术框架
- 新增 AI 框架
- 新增数据库组件
- 新增向量库
- 新增部署组件

需要重点检查：

- README.md
- docs/Tech_Stack.md
- docs/AI_Coding_Rules.md
- package.json
- requirements.txt
- docker-compose.yml

### 3. 数据库变化

包括但不限于：

- 新增表
- 删除表
- 修改字段
- 新增字段
- 删除字段
- 修改字段类型
- 新增索引
- 删除索引
- 新增约束
- 修改初始化数据
- 新增 Alembic migration

需要重点检查：

- docs/Database_Design.md
- database/schema.sql
- database/seed.sql
- backend/app/models/
- backend/app/schemas/
- README.md

### 4. 接口变化

包括但不限于：

- 新增 API
- 修改 API 路径
- 修改请求参数
- 修改返回字段
- 修改统一返回格式
- 修改错误码
- 修改鉴权方式

需要重点检查：

- docs/API_Design.md，如果存在
- README.md
- docs/PRD.md
- frontend/src/api/
- backend/app/api/
- backend/app/schemas/

### 5. 目录结构变化

包括但不限于：

- 新增目录
- 删除目录
- 文件迁移
- 模块拆分
- 重构项目结构

需要重点检查：

- docs/Project_Structure.md
- README.md
- docs/AI_Coding_Rules.md

### 6. 环境变量和部署变化

包括但不限于：

- 新增环境变量
- 修改环境变量名称
- 修改端口
- 修改 Docker 服务
- 修改数据库连接方式
- 修改前后端启动方式

需要重点检查：

- .env.example
- README.md
- docker-compose.yml
- docs/Tech_Stack.md

---

## 文档更新规则

### README.md

README.md 必须保持面向项目使用者。

当出现以下情况时必须更新：

- 项目功能变化
- 启动方式变化
- 技术栈变化
- Docker 配置变化
- API 使用方式变化
- 页面路径变化
- 环境变量变化
- 项目目录结构变化

README.md 至少应包含：

1. 项目介绍
2. 核心功能
3. 技术栈
4. 目录结构
5. 本地启动方式
6. Docker 启动方式
7. 环境变量说明
8. 当前版本功能边界
9. 后续规划

### docs/PRD.md

PRD.md 必须保持面向产品需求和功能边界。

当出现以下情况时必须更新：

- 新增功能模块
- 删除功能模块
- 修改功能流程
- 修改目标用户
- 修改项目定位
- 修改版本规划
- 修改验收标准

PRD.md 至少应包含：

1. 项目背景
2. 目标用户
3. 核心痛点
4. 产品目标
5. V1 功能范围
6. 后续版本规划
7. 不做事项
8. 验收标准

### docs/Tech_Stack.md

Tech_Stack.md 必须保持面向技术选型。

当出现以下情况时必须更新：

- 新增技术组件
- 替换技术组件
- 删除技术组件
- 新增依赖
- 修改前端、后端、数据库、AI、部署方案

Tech_Stack.md 至少应包含：

1. 前端技术栈
2. 后端技术栈
3. 数据库技术栈
4. AI / RAG 技术栈
5. 部署技术栈
6. 每个技术选型的原因
7. 不选择其他方案的原因

### docs/Database_Design.md

Database_Design.md 必须保持面向数据库设计。

当出现以下情况时必须更新：

- 新增表
- 删除表
- 修改字段
- 修改字段类型
- 新增索引
- 新增约束
- 修改实体关系
- 修改初始化数据

Database_Design.md 至少应包含：

1. 表清单
2. 每张表用途
3. 字段说明
4. 主键说明
5. 索引说明
6. 表关系说明
7. 数据字典说明
8. 后续扩展字段说明

### docs/AI_Coding_Rules.md

AI_Coding_Rules.md 必须保持面向 AI 编程规则。

当出现以下情况时必须更新：

- 新增开发规范
- 新增文档同步要求
- 新增禁止事项
- 新增代码分层规则
- 新增测试或验收要求
- 用户纠正了 Codex 的错误行为

AI_Coding_Rules.md 至少应包含：

1. 不允许随意更换技术栈
2. 不允许删除已有功能
3. 不允许引入未确认的新依赖
4. 修改代码前必须说明影响范围
5. 新增功能必须同步更新文档
6. 后端接口返回格式必须统一
7. 前端页面风格必须统一
8. 数据库结构变更必须更新 Database_Design.md
9. 接口变更必须更新 API 文档
10. 目录结构变更必须更新 Project_Structure.md

### docs/Project_Structure.md

Project_Structure.md 必须保持面向目录结构说明。

当出现以下情况时必须更新：

- 新增目录
- 删除目录
- 移动文件
- 新增模块
- 拆分模块
- 重构项目结构

Project_Structure.md 至少应包含：

1. 根目录结构
2. backend 目录说明
3. frontend 目录说明
4. database 目录说明
5. docs 目录说明
6. Docker 配置说明
7. 每个主要文件夹的职责边界

---

## 执行流程

每次接到修改任务时，必须按照以下流程执行。

### 第一步：识别修改类型

先判断本次任务属于哪些类型：

- 功能变化
- 技术栈变化
- 数据库变化
- 接口变化
- 目录结构变化
- 环境变量变化
- 部署变化
- 文档变化

### 第二步：声明影响范围

在修改前，必须先说明：

1. 本次准备修改哪些代码文件
2. 本次可能影响哪些文档
3. 哪些文档必须同步更新
4. 哪些文档预计不需要更新

### 第三步：执行代码修改

按用户需求修改代码。

要求：

1. 不要更换既定技术栈。
2. 不要破坏已有功能。
3. 不要引入未确认的新依赖。
4. 不要把所有逻辑写在一个文件里。
5. 保持前后端分层清晰。
6. 后端保持 api、schemas、models、services、core 分层。
7. 前端保持 api、components、pages、router、types 分层。

### 第四步：同步更新文档

代码修改完成后，必须根据实际变更更新对应文档。

如果本次涉及多个文档，必须全部更新。

如果某个文档看似相关但不需要更新，必须说明原因。

### 第五步：输出文档同步报告

最终回复中必须包含：

1. 本次修改的代码文件
2. 本次修改的文档文件
3. 本次未修改但已检查的文档
4. 未修改原因
5. 本次是否存在待补充文档
6. 建议的下一步

---

## 最终回复格式

每次完成任务后，必须使用以下格式回复：

### 本次完成内容

- 说明完成了哪些功能或修复。

### 代码修改文件

- 列出修改过的代码文件。

### 文档同步情况

已更新：

- README.md：说明更新了什么。
- docs/PRD.md：说明更新了什么。
- docs/Tech_Stack.md：说明更新了什么。
- docs/Database_Design.md：说明更新了什么。
- docs/AI_Coding_Rules.md：说明更新了什么。
- docs/Project_Structure.md：说明更新了什么。

已检查但未更新：

- 文件名：说明为什么不需要更新。

### 验收方式

- 说明如何运行、如何测试、如何确认本次修改成功。

### 风险与注意事项

- 说明可能存在的问题、边界或后续待处理事项。

---

## 强制规则

1. 只要代码、接口、数据库、目录、依赖、部署、配置发生变化，就必须检查文档。
2. 不允许只改代码不检查文档。
3. 不允许只说“文档无需更新”但不解释原因。
4. 不允许随意更换既定技术栈。
5. 不允许删除已有功能。
6. 不允许把真实公司数据库账号、密码、内网地址、敏感字段值写入文档或代码。
7. 不允许把真实公司业务数据写入 seed.sql。
8. 如果涉及公司数据库，只允许采集元数据，不允许采集真实业务明细数据。
9. 如果涉及外部数据源，必须强调只读、脱敏、权限和审计。
10. 如果任务需求不明确，优先做最小可行修改，不要擅自扩展复杂功能。

---

## 默认文档更新判断表

| 修改内容 | 必须更新文档 |
|---|---|
| 新增页面 | README.md、PRD.md、Project_Structure.md |
| 新增接口 | README.md、API_Design.md、PRD.md |
| 修改接口返回 | API_Design.md、README.md、前端 types |
| 新增数据库表 | Database_Design.md、schema.sql、README.md |
| 修改数据库字段 | Database_Design.md、schema.sql |
| 新增依赖 | Tech_Stack.md、README.md |
| 修改技术栈 | Tech_Stack.md、README.md、AI_Coding_Rules.md |
| 修改目录结构 | Project_Structure.md、README.md |
| 修改 Docker | README.md、Tech_Stack.md、docker-compose.yml |
| 新增环境变量 | README.md、.env.example |
| 新增 AI 模块 | PRD.md、Tech_Stack.md、AI_Coding_Rules.md |
| 新增 RAG 功能 | PRD.md、Tech_Stack.md、Database_Design.md |
| 新增数据源模块 | PRD.md、Database_Design.md、Tech_Stack.md、README.md |
| 新增 Text-to-SQL | PRD.md、Tech_Stack.md、AI_Coding_Rules.md、API_Design.md |
| 新增 SQL Agent | PRD.md、Tech_Stack.md、AI_Coding_Rules.md、Project_Structure.md |

---

## 每次任务前的自检问题

在修改前，必须自问：

1. 这次修改是否改变了用户能看到的功能？
2. 这次修改是否改变了接口？
3. 这次修改是否改变了数据库？
4. 这次修改是否改变了技术栈或依赖？
5. 这次修改是否改变了目录结构？
6. 这次修改是否改变了启动方式或部署方式？
7. 这次修改是否改变了环境变量？
8. 这次修改是否需要更新 README？
9. 这次修改是否需要更新 PRD？
10. 这次修改是否需要更新数据库设计文档？

只要任意问题答案为“是”，就必须同步更新相关文档。
