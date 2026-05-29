import { Alert, Button, Card, List, Space, Typography } from "antd";
import { SafetyCertificateOutlined } from "@ant-design/icons";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { checkSqlRisk } from "../api/sql";
import RiskTag from "../components/RiskTag";
import SqlEditor from "../components/SqlEditor";

export default function SqlRiskCheck() {
  const [sql, setSql] = useState("");
  const mutation = useMutation({ mutationFn: checkSqlRisk });

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Typography.Title level={3}>SQL 风险检查</Typography.Title>
      <Card>
        <SqlEditor value={sql} onChange={setSql} height={280} />
        <Button
          type="primary"
          icon={<SafetyCertificateOutlined />}
          loading={mutation.isPending}
          disabled={!sql.trim()}
          onClick={() => mutation.mutate(sql)}
          style={{ marginTop: 16 }}
        >
          检查风险
        </Button>
      </Card>
      {mutation.data && (
        <Card title="检查结果">
          <Space direction="vertical" size={12} style={{ width: "100%" }}>
            <div>
              风险等级：<RiskTag level={mutation.data.risk_level} />
            </div>
            <Alert
              type={mutation.data.risk_level === "HIGH" ? "error" : mutation.data.risk_level === "MEDIUM" ? "warning" : "success"}
              message={mutation.data.risk_items.length ? mutation.data.risk_items.join("；") : "未发现明显风险"}
              showIcon
            />
            <List
              header="建议"
              dataSource={mutation.data.suggestions}
              renderItem={(item) => <List.Item>{item}</List.Item>}
            />
          </Space>
        </Card>
      )}
    </Space>
  );
}
