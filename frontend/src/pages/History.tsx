import { Button, Drawer, Space, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getHistory } from "../api/history";
import RiskTag from "../components/RiskTag";
import type { SqlHistoryItem } from "../types/sql";

export default function History() {
  const [current, setCurrent] = useState<SqlHistoryItem | null>(null);
  const { data, isLoading } = useQuery({ queryKey: ["history"], queryFn: getHistory });

  const columns: ColumnsType<SqlHistoryItem> = [
    { title: "创建时间", dataIndex: "created_at", width: 200, render: (value) => new Date(value).toLocaleString() },
    { title: "SQL 类型", dataIndex: "sql_type", width: 120 },
    { title: "风险等级", dataIndex: "risk_level", width: 120, render: (value) => <RiskTag level={value} /> },
    { title: "SQL 摘要", dataIndex: "summary", ellipsis: true },
    { title: "操作", width: 100, render: (_, record) => <Button type="link" onClick={() => setCurrent(record)}>详情</Button> }
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>历史记录</Typography.Title>
      <Table rowKey="id" loading={isLoading} dataSource={data || []} columns={columns} pagination={{ pageSize: 10 }} />
      <Drawer title="分析详情" open={!!current} width={720} onClose={() => setCurrent(null)}>
        {current && (
          <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <div>
              <Typography.Text type="secondary">风险等级：</Typography.Text>
              <RiskTag level={current.risk_level} />
            </div>
            <Typography.Title level={5}>SQL</Typography.Title>
            <pre style={{ background: "#f5f5f5", padding: 12, overflow: "auto" }}>{current.raw_sql}</pre>
            <Typography.Title level={5}>摘要</Typography.Title>
            <Typography.Paragraph>{current.summary}</Typography.Paragraph>
            <Typography.Title level={5}>完整 JSON</Typography.Title>
            <pre style={{ background: "#f5f5f5", padding: 12, overflow: "auto" }}>
              {JSON.stringify(current.analysis_result_json, null, 2)}
            </pre>
          </Space>
        )}
      </Drawer>
    </Space>
  );
}
