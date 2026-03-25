import { NavLink } from "react-router-dom";
import { MODULES, UTILITY_LINKS } from "../constants";
import ProjectSelector from "./ProjectSelector";

export default function TopNav() {
  return (
    <nav
      style={{
        background: "var(--color-navy)",
        padding: "0 24px",
        display: "flex",
        alignItems: "center",
        height: 56,
        gap: 8,
        flexShrink: 0,
      }}
    >
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginRight: 32 }}>
        <span
          style={{
            color: "#fff",
            fontSize: 17,
            fontWeight: 900,
            letterSpacing: "-0.3px",
          }}
        >
          J-Braze Studio
        </span>
      </div>

      {/* Module tabs (center) */}
      <div style={{ display: "flex", gap: 4, flex: 1 }}>
        {MODULES.map((mod) => (
          <NavLink
            key={mod.id}
            to={mod.path}
            style={({ isActive }) => ({
              color: isActive ? "#fff" : "rgba(255,255,255,0.55)",
              background: isActive ? "rgba(255,255,255,0.1)" : "transparent",
              padding: "8px 16px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
              textDecoration: "none",
              transition: "all 0.15s",
              borderBottom: isActive ? "2px solid var(--color-red)" : "2px solid transparent",
            })}
          >
            {mod.label}
          </NavLink>
        ))}
      </div>

      {/* Project selector + Utility links (right) */}
      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <ProjectSelector />
        <div style={{ width: 1, height: 24, background: "rgba(255,255,255,0.12)", margin: "0 8px" }} />
        {UTILITY_LINKS.map((link) => (
          <NavLink
            key={link.id}
            to={link.path}
            style={({ isActive }) => ({
              color: isActive ? "#fff" : "rgba(255,255,255,0.5)",
              fontSize: 13,
              fontWeight: 500,
              textDecoration: "none",
              padding: "6px 12px",
              borderRadius: 6,
              transition: "all 0.15s",
              background: isActive ? "rgba(255,255,255,0.08)" : "transparent",
            })}
          >
            {link.label}
          </NavLink>
        ))}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            color: "rgba(255,255,255,0.4)",
            marginLeft: 12,
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "var(--color-success)",
              display: "inline-block",
            }}
          />
          v1.0
        </div>
      </div>
    </nav>
  );
}
