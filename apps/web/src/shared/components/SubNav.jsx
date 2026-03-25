import { NavLink, useLocation } from "react-router-dom";
import { SUB_NAV_ITEMS } from "../constants";

export default function SubNav({ children }) {
  const location = useLocation();
  const currentModule = location.pathname.split("/")[1] || "";
  const items = SUB_NAV_ITEMS[currentModule];

  if (!items && !children) return null;

  return (
    <div
      style={{
        background: "var(--color-surface)",
        borderBottom: "1px solid var(--color-border)",
        padding: "0 24px",
        display: "flex",
        gap: 4,
        height: 44,
        alignItems: "center",
        flexShrink: 0,
      }}
    >
      {children
        ? children
        : items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end
              style={({ isActive }) => ({
                color: isActive ? "var(--color-navy)" : "var(--color-text-muted)",
                borderBottom: isActive
                  ? "2px solid var(--color-red)"
                  : "2px solid transparent",
                padding: "10px 14px",
                fontSize: 13,
                fontWeight: 600,
                textDecoration: "none",
                transition: "all 0.15s",
                marginBottom: -1,
              })}
            >
              {item.label}
            </NavLink>
          ))}
    </div>
  );
}
