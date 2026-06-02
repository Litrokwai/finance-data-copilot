import { AuditOutlined, BranchesOutlined, DashboardOutlined, DatabaseOutlined, HistoryOutlined, SafetyCertificateOutlined, TableOutlined } from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

const { Header, Sider, Content } = Layout;

const items = [
  { key: "/dashboard", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/metadata", icon: <TableOutlined />, label: "元数据全景" },
  { key: "/procedure-lineage", icon: <BranchesOutlined />, label: "存储过程血缘" },
  { key: "/lineage-review", icon: <AuditOutlined />, label: "血缘复核" },
  { key: "/sql-analyze", icon: <DatabaseOutlined />, label: "SQL 解释" },
  { key: "/sql-risk-check", icon: <SafetyCertificateOutlined />, label: "SQL 风险检查" },
  { key: "/history", icon: <HistoryOutlined />, label: "历史记录" }
];

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider width={232} theme="dark">
        <div style={{ height: 64, display: "flex", alignItems: "center", padding: "0 20px" }}>
          <Typography.Text style={{ color: "#fff", fontWeight: 700, fontSize: 16 }}>Finance Data Copilot</Typography.Text>
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={items} onClick={({ key }) => navigate(key)} />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", borderBottom: "1px solid #f0f0f0", padding: "0 24px" }}>
          <Typography.Text type="secondary">金融数据 AI 开发助手</Typography.Text>
        </Header>
        <Content style={{ padding: 24, background: "#f5f7fa" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
