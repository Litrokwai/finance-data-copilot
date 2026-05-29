import { Card, Empty, Space, Tag, Typography } from "antd";
import RiskTag from "./RiskTag";
import type { SqlAnalyzeResult } from "../types/sql";

const { Paragraph, Text } = Typography;

export default function ResultCard({ result }: { result?: SqlAnalyzeResult }) {
  if (!result) {
    return <Empty description="暂无分析结果" />;
  }

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Card title="SQL 总结" size="small">
        <Paragraph>{result.summary}</Paragraph>
        <Space>
          <Text type="secondary">SQL 类型</Text>
          <Tag color="blue">{result.sql_type}</Tag>
          <Text type="secondary">风险等级</Text>
          <RiskTag level={result.risk_level} />
        </Space>
      </Card>

      <Card title="结构解析" size="small">
        <Paragraph>
          <Text strong>涉及表：</Text>
          {result.involved_tables.length ? result.involved_tables.map((item) => <Tag key={item}>{item}</Tag>) : "无"}
        </Paragraph>
        <Paragraph>
          <Text strong>涉及字段：</Text>
          {result.involved_columns.length ? result.involved_columns.map((item) => <Tag key={item}>{item}</Tag>) : "无"}
        </Paragraph>
        <Paragraph>
          <Text strong>JOIN 关系：</Text>
          {result.join_relations.length
            ? result.join_relations.map((item, index) => (
                <Tag key={`${item.table}-${index}`}>{`${item.join_type} ${item.table} ON ${item.on || "无"}`}</Tag>
              ))
            : "无"}
        </Paragraph>
        <Paragraph>
          <Text strong>WHERE 条件：</Text>
          {result.where_conditions.length ? result.where_conditions.map((item) => <Tag key={item}>{item}</Tag>) : "无"}
        </Paragraph>
      </Card>

      <Card title="风险与建议" size="small">
        <Paragraph>
          <Text strong>风险项：</Text>
          {result.risk_items.length ? result.risk_items.map((item) => <Tag color="volcano" key={item}>{item}</Tag>) : "无明显风险"}
        </Paragraph>
        <ul>
          {result.suggestions.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Card>
    </Space>
  );
}
