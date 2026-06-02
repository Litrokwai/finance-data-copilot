# API Design

后端接口统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## SQL 分析

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/sql/analyze` | 解析 SQL 类型、表、字段、JOIN、WHERE 和风险，并保存历史记录 |
| POST | `/api/sql/risk-check` | 对输入 SQL 做基础风险检查 |

## 历史记录

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/history` | 返回最近 SQL 分析历史 |

## Dashboard

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/dashboard/summary` | 返回 SQL 分析数量、风险分布和趋势 |

## 元数据全景

元数据接口只读取本项目 PostgreSQL 中已同步的 `metadata_table`、`metadata_column` 和 `metric_definition`，不读取公司真实业务明细数据。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/metadata/summary` | 返回表、字段、指标、业务域分布、敏感字段和 Top 表统计 |
| GET | `/api/metadata/tables` | 分页查询表资产，支持 `keyword`、`business_domain`、`is_valid`、`sort_by`、`sort_order`、`page`、`page_size` |
| GET | `/api/metadata/tables/{table_id}` | 返回单表详情、字段列表和关联指标 |
| GET | `/api/metadata/graph` | 返回好股库元数据、业务域和表的层级矩形图数据，业务域和表节点按字段规模展示 |

`/api/metadata/tables` 查询参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| keyword | string | 按表名、说明、业务域或负责人模糊搜索 |
| business_domain | string | 按业务域过滤 |
| is_valid | boolean | 按可用状态过滤 |
| sort_by | string | 服务端排序字段，支持 `table_name`、`table_comment`、`business_domain`、`column_count`、`sensitive_column_count`、`updated_at` |
| sort_order | string | 排序方向，支持 `asc`、`desc` |
| page | integer | 页码，默认 1 |
| page_size | integer | 每页数量，默认 20，最大 100 |

当不传 `sort_by` 和 `sort_order` 时，默认按可用状态、业务域、字段数从高到低排序，再进行分页。

单表详情中的字段列表返回字段序号、字段名、数据类型、字段中文名、字段备注、主键、是否为空、敏感标记和状态。字段列表按源端 `catalog_columns.ordinal_position` 排序；字段备注由前端以提示形式展示，不单独占用表格列。

## 存储过程血缘

血缘接口只读取本项目 PostgreSQL 中已同步的 `procedure_lineage_record`，不连接公司业务库，不执行存储过程或用户输入 SQL。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/lineage/summary` | 返回已同步过程数量、读取表数量、写入表数量、结构化血缘边数量、需复核数量和最近同步时间 |
| GET | `/api/lineage/procedures` | 返回存储过程血缘列表，支持 `keyword` 按过程名或涉及表搜索，支持 `parse_status=SUCCESS/REVIEW` 按解析状态筛选 |
| GET | `/api/lineage/procedures/{record_id}` | 返回单个过程的读取表、写入表、临时表、旧版边和结构化血缘边详情 |
| GET | `/api/lineage/tables` | 返回血缘中涉及的数据表列表，支持 `keyword` 和 `limit`，用于表影响分析入口 |
| GET | `/api/lineage/table-impact` | 返回单表影响范围，参数 `table_name`，包括读取该表的过程、写入该表的过程和相关表间链路 |
| GET | `/api/lineage/graph` | 返回前端关系图使用的过程节点、表节点和 READ/WRITE 边，支持 `keyword`、`parse_status` 和 `max_procedures` |

`parse_status` 当前支持 `SUCCESS` 和 `REVIEW`。结构化血缘边包括 `READ`、`WRITE` 和 `TABLE_FLOW` 三类。`READ/WRITE` 表示过程与表的关系，`TABLE_FLOW` 表示同一语句中由读取对象推导到写入对象的表间链路。动态 SQL 会将过程标记为 `REVIEW`，结果需要人工复核；详情接口会返回复核原因和语句片段，用于人工判断。表影响分析只读取已同步的本地血缘缓存，并会过滤明显的 SQL 别名噪声；同一表名的大小写差异会按大小写不敏感规则合并，读取过程和写入过程按存储过程去重统计。
