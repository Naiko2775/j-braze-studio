import { useState } from "react";

/**
 * Composant d'onglets reutilisable.
 * Usage:
 *   <ResultTabs tabs={[
 *     { id: "data", label: "Donnees", content: <DataView /> },
 *     { id: "json", label: "JSON", content: <JsonView /> },
 *   ]} />
 */
export default function ResultTabs({ tabs, defaultTab }) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id);
  const activeTab = tabs.find((t) => t.id === active);

  return (
    <div>
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${active === tab.id ? "active" : ""}`}
            onClick={() => setActive(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div style={{ padding: "20px 0" }}>{activeTab?.content}</div>
    </div>
  );
}
