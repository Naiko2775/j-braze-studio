import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { API_BASE } from "../constants";

const ProjectContext = createContext(null);

const STORAGE_KEY = "jbraze_current_project_id";

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProjectState] = useState(null);
  const [loading, setLoading] = useState(false);

  const refreshProjects = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        return data;
      }
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
    return [];
  }, []);

  const setCurrentProject = useCallback((project) => {
    setCurrentProjectState(project);
    if (project) {
      localStorage.setItem(STORAGE_KEY, project.id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  // Initial load: fetch projects and restore selection from localStorage
  useEffect(() => {
    refreshProjects().then((list) => {
      const savedId = localStorage.getItem(STORAGE_KEY);
      if (savedId && list.length > 0) {
        const found = list.find((p) => p.id === savedId);
        if (found) {
          setCurrentProjectState(found);
        }
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <ProjectContext.Provider
      value={{
        projects,
        currentProject,
        setCurrentProject,
        refreshProjects,
        loading,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return ctx;
}
