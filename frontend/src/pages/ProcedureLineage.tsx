import {
  ApartmentOutlined,
  BranchesOutlined,
  DatabaseOutlined,
  FieldTimeOutlined,
  SearchOutlined,
  TableOutlined,
  WarningOutlined
} from "@ant-design/icons";
import { Alert, Card, Col, Descriptions, Drawer, Empty, Input, Row, Select, Space, Statistic, Table, Tag, Tooltip, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useQuery } from "@tanstack/react-query";
import * as echarts from "echarts";
import { useEffect, useRef, useState } from "react";
import {
  getLineageGraph,
  getLineageSummary,
  getLineageTableImpact,
  getLineageTables,
  getProcedureLineageDetail,
  getProcedureLineageList
} from "../api/lineage";
import type { LineageGraphNode, LineageTableUsage, ProcedureLineageEdge, ProcedureLineageItem, ProcedureRef } from "../types/lineage";

const chartFontFamily = '"Segoe UI", "Microsoft YaHei", "PingFang SC", Arial, sans-serif';

function parseStatusTag(status: string) {
  return status === "SUCCESS" ? <Tag color="green">已解析</Tag> : <Tag color="orange">需复核</Tag>;
}

function relationTag(value: string) {
  if (value === "READ") return <Tag>读取</Tag>;
  if (value === "WRITE") return <Tag color="cyan">写入</Tag>;
  return <Tag color="purple">表间链路</Tag>;
}

export default function ProcedureLineage() {
  const graphRef = useRef<HTMLDivElement | null>(null);
  const [currentProcedure, setCurrentProcedure] = useState<ProcedureLineageItem | null>(null);
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<"SUCCESS" | "REVIEW" | undefined>();
  const [tableKeyword, setTableKeyword] = useState("");
  const [selectedTable, setSelectedTable] = useState("");
  const summaryQuery = useQuery({ queryKey: ["lineage-summary"], queryFn: getLineageSummary });
  const listQuery = useQuery({
    queryKey: ["lineage-procedures", keyword, statusFilter],
    queryFn: () => getProcedureLineageList({ keyword: keyword || undefined, parse_status: statusFilter })
  });
  const graphQuery = useQuery({
    queryKey: ["lineage-graph", keyword, statusFilter],
    queryFn: () =>
      getLineageGraph({
        keyword: keyword || undefined,
        parse_status: statusFilter,
        max_procedures: statusFilter === "REVIEW" ? 120 : 80
      })
  });
  const tableListQuery = useQuery({
    queryKey: ["lineage-tables", tableKeyword],
    queryFn: () => getLineageTables({ keyword: tableKeyword || undefined, limit: 200 })
  });
  const tableImpactQuery = useQuery({
    queryKey: ["lineage-table-impact", selectedTable],
    queryFn: () => getLineageTableImpact(selectedTable),
    enabled: !!selectedTable
  });
  const detailQuery = useQuery({
    queryKey: ["lineage-procedure-detail", currentProcedure?.id],
    queryFn: () => getProcedureLineageDetail(currentProcedure!.id),
    enabled: !!currentProcedure
  });

  function openProcedureByRef(record: ProcedureRef) {
    setCurrentProcedure({
      id: record.procedure_id,
      procedure_name: record.procedure_name,
      read_table_count: 0,
      write_table_count: 0,
      temp_table_count: 0,
      edge_count: 0,
      table_flow_count: 0,
      statement_count: 0,
      parse_status: "SUCCESS"
    });
  }

  useEffect(() => {
    if (!graphRef.current || !graphQuery.data) return;
    const chart = echarts.init(graphRef.current);
    chart.setOption({
      textStyle: { fontFamily: chartFontFamily },
      color: ["#3568d4", "#6b879c", "#287c89"],
      tooltip: {
        trigger: "item",
        formatter: (params: { data?: LineageGraphNode; dataType?: string; name?: string; value?: string; marker?: string }) => {
          if (params.dataType === "edge") return `${params.marker || ""}${params.value || ""}`;
          const data = params.data as LineageGraphNode & { nodeCategory?: LineageGraphNode["category"] };
          const category = data?.nodeCategory || data?.category;
          return `
            <div class="metadata-chart-tooltip">
              <div class="metadata-chart-tooltip-title">${data?.name || params.name}</div>
              <div>${data?.full_name || ""}</div>
              <div>类型：${category === "procedure" ? "存储过程" : "数据表"}</div>
            </div>
          `;
        }
      },
      legend: [{ data: ["存储过程", "读取表", "写入表", "临时表"], top: 0 }],
      series: [
        {
          type: "graph",
          layout: "force",
          top: 40,
          roam: true,
          draggable: true,
          categories: [{ name: "存储过程" }, { name: "读取表" }, { name: "写入表" }, { name: "临时表" }],
          data: graphQuery.data.nodes.map((node) => ({
            ...node,
            nodeCategory: node.category,
            category: node.category === "procedure" ? 0 : node.category === "read_table" ? 1 : node.category === "write_table" ? 2 : 3,
            label: { show: true, formatter: "{b}", fontSize: node.category === "procedure" ? 12 : 11 }
          })),
          links: graphQuery.data.edges.map((edge) => ({
            source: edge.source,
            target: edge.target,
            value: edge.relation === "READ" ? "读取" : "写入",
            lineStyle: { color: edge.relation === "READ" ? "#9aa8b5" : "#287c89", width: edge.relation === "WRITE" ? 2 : 1.2 },
            label: { show: true, formatter: edge.relation === "READ" ? "读" : "写", fontSize: 10 }
          })),
          force: { repulsion: 280, edgeLength: [80, 180], gravity: 0.08 },
          edgeSymbol: ["none", "arrow"],
          edgeSymbolSize: 8,
          lineStyle: { curveness: 0.12 },
          emphasis: { focus: "adjacency" }
        }
      ]
    });
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [graphQuery.data]);

  const columns: ColumnsType<ProcedureLineageItem> = [
    { title: "存储过程", dataIndex: "procedure_name", ellipsis: true },
    { title: "Schema", dataIndex: "procedure_schema", width: 100 },
    { title: "读取表", dataIndex: "read_table_count", width: 100 },
    { title: "写入表", dataIndex: "write_table_count", width: 100 },
    { title: "临时表", dataIndex: "temp_table_count", width: 100 },
    { title: "血缘边", dataIndex: "edge_count", width: 100 },
    { title: "表间链路", dataIndex: "table_flow_count", width: 100 },
    { title: "语句数", dataIndex: "statement_count", width: 100 },
    { title: "状态", dataIndex: "parse_status", width: 100, render: parseStatusTag },
    {
      title: "操作",
      width: 96,
      render: (_, record) => (
        <Typography.Link onClick={() => setCurrentProcedure(record)}>
          详情
        </Typography.Link>
      )
    }
  ];

  const edgeColumns: ColumnsType<ProcedureLineageEdge> = [
    { title: "序号", dataIndex: "statement_index", width: 72 },
    { title: "关系", dataIndex: "relation_type", width: 100, render: relationTag },
    { title: "来源", dataIndex: "source_object", ellipsis: true },
    { title: "目标", dataIndex: "target_object", ellipsis: true },
    { title: "语句类型", dataIndex: "statement_type", width: 96 },
    { title: "置信度", dataIndex: "confidence", width: 96, render: (value: number) => `${Math.round(value * 100)}%` },
    {
      title: "语句片段",
      dataIndex: "statement_snippet",
      width: 220,
      ellipsis: true,
      render: (value?: string) =>
        value ? (
          <Tooltip title={value}>
            <Typography.Text ellipsis>{value}</Typography.Text>
          </Tooltip>
        ) : (
          "-"
        )
    }
  ];

  const tableUsageColumns: ColumnsType<LineageTableUsage> = [
    {
      title: "表名",
      dataIndex: "table_name",
      ellipsis: true,
      render: (value: string) => <Typography.Link onClick={() => setSelectedTable(value)}>{value}</Typography.Link>
    },
    { title: "读取过程", dataIndex: "read_by_count", width: 96 },
    { title: "写入过程", dataIndex: "write_by_count", width: 96 },
    { title: "血缘边", dataIndex: "edge_count", width: 88 }
  ];

  const procedureRefColumns: ColumnsType<ProcedureRef> = [
    {
      title: "存储过程",
      dataIndex: "procedure_name",
      ellipsis: true,
      render: (value: string, record) => <Typography.Link onClick={() => openProcedureByRef(record)}>{value}</Typography.Link>
    }
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>存储过程血缘</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6} xl={4}>
          <Card>
            <Statistic title="过程数量" value={summaryQuery.data?.total_procedures || 0} prefix={<BranchesOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={4}>
          <Card>
            <Statistic title="读取表" value={summaryQuery.data?.total_read_tables || 0} prefix={<DatabaseOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={4}>
          <Card>
            <Statistic title="写入表" value={summaryQuery.data?.total_write_tables || 0} prefix={<TableOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={4}>
          <Card>
            <Statistic title="血缘边" value={summaryQuery.data?.total_edges || 0} prefix={<ApartmentOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} xl={4}>
          <Card hoverable onClick={() => setStatusFilter("REVIEW")}>
            <Statistic
              title="需复核"
              value={summaryQuery.data?.review_count || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: "#d46b08" }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="过程与表关系图"
        extra={
          <Space wrap>
            {statusFilter === "REVIEW" && <Tag color="orange">当前仅看需复核</Tag>}
            <Tag icon={<FieldTimeOutlined />}>仅基于定义解析，不执行过程</Tag>
          </Space>
        }
      >
        {graphQuery.data?.nodes.length ? <div className="lineage-graph-chart" ref={graphRef} /> : <Empty description="当前筛选条件下暂无血缘数据" />}
      </Card>

      <Card
        title="存储过程列表"
        extra={
          <Space wrap>
            <Input.Search
              allowClear
              enterButton={<SearchOutlined />}
              placeholder="搜索过程名或涉及表"
              style={{ width: 260 }}
              onSearch={(value) => setKeyword(value.trim())}
            />
            <Select
              allowClear
              placeholder="解析状态"
              style={{ width: 140 }}
              value={statusFilter}
              onChange={(value?: "SUCCESS" | "REVIEW") => setStatusFilter(value)}
              options={[
                { label: "已解析", value: "SUCCESS" },
                { label: "需复核", value: "REVIEW" }
              ]}
            />
          </Space>
        }
      >
        <Table rowKey="id" loading={listQuery.isLoading} dataSource={listQuery.data || []} columns={columns} pagination={{ pageSize: 20 }} />
      </Card>

      <Card
        title="表影响分析"
        extra={
          <Input.Search
            allowClear
            enterButton={<SearchOutlined />}
            placeholder="搜索表名后在列表中选择"
            style={{ width: 300 }}
            onSearch={(value) => {
              setTableKeyword(value.trim());
            }}
          />
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={10}>
            <Table
              rowKey="table_name"
              size="small"
              loading={tableListQuery.isLoading}
              dataSource={tableListQuery.data || []}
              columns={tableUsageColumns}
              pagination={{ pageSize: 8 }}
            />
          </Col>
          <Col xs={24} lg={14}>
            {selectedTable ? (
              <Space direction="vertical" size={12} style={{ width: "100%" }}>
                <Descriptions bordered size="small" column={3}>
                  <Descriptions.Item label="当前表" span={3}>
                    <Typography.Text copyable>{tableImpactQuery.data?.table_name || selectedTable}</Typography.Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="读取过程">{tableImpactQuery.data?.read_by_procedures.length || 0}</Descriptions.Item>
                  <Descriptions.Item label="写入过程">{tableImpactQuery.data?.write_by_procedures.length || 0}</Descriptions.Item>
                  <Descriptions.Item label="表间链路">{tableImpactQuery.data?.table_flow_edges.length || 0}</Descriptions.Item>
                </Descriptions>
                <Row gutter={[12, 12]}>
                  <Col xs={24} md={12}>
                    <Table
                      rowKey="procedure_id"
                      size="small"
                      title={() => "读取该表的过程"}
                      loading={tableImpactQuery.isLoading}
                      dataSource={tableImpactQuery.data?.read_by_procedures || []}
                      columns={procedureRefColumns}
                      pagination={{ pageSize: 6 }}
                    />
                  </Col>
                  <Col xs={24} md={12}>
                    <Table
                      rowKey="procedure_id"
                      size="small"
                      title={() => "写入该表的过程"}
                      loading={tableImpactQuery.isLoading}
                      dataSource={tableImpactQuery.data?.write_by_procedures || []}
                      columns={procedureRefColumns}
                      pagination={{ pageSize: 6 }}
                    />
                  </Col>
                </Row>
                <Table
                  rowKey="id"
                  size="small"
                  title={() => "相关表间链路"}
                  loading={tableImpactQuery.isLoading}
                  dataSource={tableImpactQuery.data?.table_flow_edges || []}
                  columns={edgeColumns}
                  pagination={{ pageSize: 6 }}
                />
              </Space>
            ) : (
              <Empty description="请选择左侧表，或输入表名查看影响范围" />
            )}
          </Col>
        </Row>
      </Card>

      <Drawer title="血缘详情" open={!!currentProcedure} width={820} onClose={() => setCurrentProcedure(null)}>
        {detailQuery.data && (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            {detailQuery.data.parse_status === "REVIEW" && (
              <Alert
                showIcon
                type="warning"
                message="需要人工复核"
                description={detailQuery.data.parse_message || "检测到动态 SQL、变量表名或复杂语句，当前血缘结果仅作为辅助参考。"}
              />
            )}
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="存储过程" span={2}>{detailQuery.data.procedure_name}</Descriptions.Item>
              <Descriptions.Item label="Schema">{detailQuery.data.procedure_schema || "-"}</Descriptions.Item>
              <Descriptions.Item label="解析状态">{parseStatusTag(detailQuery.data.parse_status)}</Descriptions.Item>
              <Descriptions.Item label="语句数">{detailQuery.data.statement_count}</Descriptions.Item>
              <Descriptions.Item label="同步时间">{detailQuery.data.synced_at || "-"}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="读取表">
              <Space wrap>{detailQuery.data.read_tables.map((table) => <Tag key={table}>{table}</Tag>)}</Space>
            </Card>
            <Card size="small" title="写入表">
              <Space wrap>{detailQuery.data.write_tables.map((table) => <Tag color="cyan" key={table}>{table}</Tag>)}</Space>
            </Card>
            <Card size="small" title="临时表">
              <Space wrap>{detailQuery.data.temp_tables.length ? detailQuery.data.temp_tables.map((table) => <Tag color="default" key={table}>{table}</Tag>) : "-"}</Space>
            </Card>
            <Table
              rowKey="id"
              size="small"
              title={() => "结构化血缘边"}
              dataSource={detailQuery.data.structured_edges}
              columns={edgeColumns}
              pagination={{ pageSize: 10 }}
            />
          </Space>
        )}
      </Drawer>
    </Space>
  );
}
