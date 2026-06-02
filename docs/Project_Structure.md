# Project Structure

```text
finance-data-copilot/
├── backend/
│   ├── app/
│   │   ├── api/        # FastAPI 路由
│   │   ├── core/       # 配置和数据库连接
│   │   ├── models/     # SQLAlchemy 模型
│   │   ├── schemas/    # Pydantic 请求响应结构
│   │   ├── services/   # 业务逻辑
│   │   ├── connectors/ # 外部数据源只读连接器
│   │   ├── ai/         # 大模型调用封装和 prompt
│   │   └── main.py     # FastAPI 入口
│   ├── alembic/        # 数据库迁移
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/        # Axios 请求封装和接口模块
│   │   ├── components/ # 通用组件
│   │   ├── pages/      # 页面
│   │   ├── router/     # 路由配置
│   │   ├── types/      # TypeScript 类型
│   │   ├── App.tsx     # 应用布局
│   │   └── main.tsx    # 前端入口
│   └── package.json
├── database/           # 初始化 schema 和空 seed 占位
├── docs/               # 项目文档，包含 PRD、API、数据库设计、技术栈和 Product_Status
├── scripts/            # 本地启动、数据库初始化和元数据同步脚本
├── docker-compose.yml
├── .env.example
└── README.md
```

后端采用 API、service、model、schema、connector 分层，避免把所有逻辑写在单个文件。元数据全景和元数据质量由 `backend/app/api/routes_metadata.py`、`backend/app/services/metadata_service.py` 和 `backend/app/schemas/metadata.py` 组成，其中字段详情排序在 `metadata_service.py` 中按源端 `ordinal_position` 维护，元数据质量统计基于本地 `metadata_table`、`metadata_column` 和 `procedure_lineage_edge` 聚合。存储过程血缘由 `backend/app/api/routes_lineage.py`、`backend/app/services/procedure_lineage_service.py`、`backend/app/models/procedure_lineage_record.py`、`backend/app/models/procedure_lineage_edge.py`、`backend/app/models/lineage_review_record.py` 和 `backend/app/schemas/lineage.py` 组成，过程列表、关系图、表影响分析和血缘复核工作台均读取本地 PostgreSQL 血缘缓存。前端采用页面、组件、请求和类型分层，`frontend/src/pages/MetadataPanorama.tsx`、`frontend/src/pages/MetadataQuality.tsx`、`frontend/src/api/metadata.ts` 和 `frontend/src/types/metadata.ts` 负责元数据全景和质量页面，`frontend/src/pages/ProcedureLineage.tsx`、`frontend/src/pages/LineageReview.tsx`、`frontend/src/api/lineage.ts` 和 `frontend/src/types/lineage.ts` 负责存储过程血缘和血缘复核页面。`docs/Product_Status.md` 负责记录当前产品目的、数据规模、开发主线和下一步优先级。`scripts/sync_howgow_metadata.py` 负责从公司 SQL Server 的 `ai_platform` 元数据表只读同步好股库表、字段、指标口径和源端时间信号。`scripts/sync_data_dictionary_details.py` 负责从数据字典网页接口同步真实主键和少数字段备注。`scripts/sync_procedure_lineage.py` 负责通过链接服务器只读、分批同步好股库存储过程定义并解析血缘。`scripts/import_company_metadata.py` 是早期本地文件导入路线，现在仅保留废弃提示，不再具备写入公司元数据的能力。
