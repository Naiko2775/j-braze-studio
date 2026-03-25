import { Outlet } from "react-router-dom";
import TopNav from "./TopNav";
import SubNav from "./SubNav";

export default function Layout() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopNav />
      <SubNav />
      <main
        style={{
          flex: 1,
          padding: "24px 24px",
          maxWidth: 1200,
          margin: "0 auto",
          width: "100%",
        }}
      >
        <Outlet />
      </main>
      <footer
        style={{
          padding: "12px 24px",
          textAlign: "center",
          fontSize: 12,
          color: "var(--color-text-muted)",
          borderTop: "1px solid var(--color-border)",
        }}
      >
        made with love by{" "}
        <strong style={{ color: "var(--color-navy)" }}>JAKALA</strong> -- Data,
        AI & Experiences
      </footer>
    </div>
  );
}
