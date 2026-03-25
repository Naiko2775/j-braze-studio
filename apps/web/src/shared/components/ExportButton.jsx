/**
 * Bouton d'export qui telecharge un fichier.
 * Usage: <ExportButton data={jsonObj} filename="export.json" label="Exporter JSON" />
 */
export default function ExportButton({
  data,
  filename,
  label = "Exporter",
  format = "json",
}) {
  const handleExport = () => {
    let content, mimeType;

    if (format === "json") {
      content =
        typeof data === "string" ? data : JSON.stringify(data, null, 2);
      mimeType = "application/json";
    } else {
      content = String(data);
      mimeType = "text/plain";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <button className="btn btn-secondary" onClick={handleExport}>
      {label}
    </button>
  );
}
