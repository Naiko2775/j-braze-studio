export const MODULES = [
  { id: "data-model", label: "Data Model", path: "/data-model" },
  { id: "liquid", label: "Liquid Generator", path: "/liquid" },
  { id: "migration", label: "Migration", path: "/migration" },
];

export const UTILITY_LINKS = [
  { id: "projects", label: "Projets", path: "/projects" },
  { id: "explorer", label: "Explorer", path: "/explorer" },
  { id: "history", label: "Historique", path: "/history" },
  { id: "settings", label: "\u2699\uFE0F", path: "/settings" },
];

export const SUB_NAV_ITEMS = {
  "data-model": [
    { label: "Analyser", path: "/data-model" },
    { label: "Explorateur", path: "/data-model/explorer" },
  ],
  liquid: [
    { label: "Generer", path: "/liquid" },
    { label: "Historique", path: "/history" },
  ],
  migration: [
    { label: "Configurer", path: "/migration" },
    { label: "Historique", path: "/history" },
  ],
  explorer: [
    { label: "Explorateur Braze", path: "/explorer" },
  ],
  history: [
    { label: "Historique", path: "/history" },
  ],
  settings: [
    { label: "Parametres", path: "/settings" },
  ],
};

export const API_BASE = "/api";
