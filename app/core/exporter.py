"""Export functionality for data and reports."""
import base64
from io import BytesIO
from datetime import datetime

import pandas as pd
from app.core.data_manager import DataManager
from app.core.export_manager import ExportManager


class DataExporter:
    """Export DataFrame to CSV, Excel, and HTML report."""

    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.manager = ExportManager()

    # ── CSV ────────────────────────────────────────────────────────────

    def to_csv(
        self,
        path: str,
        columns=None,
        separator: str = ",",
        encoding: str = "utf-8",
    ) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "csv", separator=separator, encoding=encoding)

    # ── Excel ──────────────────────────────────────────────────────────

    def to_excel(self, path: str, columns=None, sheet_name: str = "Datos") -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}

        df = self.dm.df[columns] if columns else self.dm.df

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            from app.core.statistics import StatisticsEngine

            stats_engine = StatisticsEngine(self.dm)
            desc = stats_engine.descriptive_stats()
            if not desc.empty:
                desc.to_excel(writer, sheet_name="Estadísticas")

            missing = stats_engine.missing_analysis()
            if not missing.empty:
                missing.to_excel(writer, sheet_name="Valores Faltantes", index=False)

        return {"success": True, "path": path, "rows": len(df), "cols": len(df.columns)}

    def to_json(self, path: str, columns=None, lines: bool = False) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "jsonl" if lines else "json", lines=lines)

    def to_html(self, path: str, columns=None) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "html")

    def to_parquet(self, path: str, columns=None) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "parquet")

    def to_xml(self, path: str, columns=None) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "xml")

    def to_yaml(self, path: str, columns=None) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "yaml")

    def to_feather(self, path: str, columns=None) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}
        df = self.dm.df[columns] if columns else self.dm.df
        return self.manager.export_dataframe(df, path, "feather")

    # ── HTML report ────────────────────────────────────────────────────

    def to_html_report(self, path: str) -> dict:
        if not self.dm.has_data():
            return {"success": False, "error": "No hay datos"}

        from app.core.statistics import StatisticsEngine
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns

        stats = StatisticsEngine(self.dm)
        info = self.dm.get_info()
        desc = stats.descriptive_stats()
        missing = stats.missing_analysis()
        corr = stats.correlation_matrix()

        charts: list[tuple[str, str]] = []

        # ── Missing values bar chart ──
        if missing["Faltantes"].sum() > 0:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")
            cols_m = missing[missing["Faltantes"] > 0]
            ax.barh(cols_m["Columna"], cols_m["% Faltantes"], color="#6366F1")
            ax.set_xlabel("% Faltantes", color="#94A3B8")
            ax.set_title("Valores Faltantes por Columna", color="#F1F5F9", fontsize=14)
            ax.tick_params(colors="#94A3B8")
            for spine in ax.spines.values():
                spine.set_color("#2D3344")
            plt.tight_layout()
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            charts.append(("Valores Faltantes",
                           base64.b64encode(buf.getvalue()).decode()))
            plt.close(fig)

        # ── Correlation heatmap ──
        if not corr.empty and len(corr) > 1:
            fig, ax = plt.subplots(figsize=(10, 8))
            fig.patch.set_facecolor("#0F1117")
            ax.set_facecolor("#0F1117")
            sns.heatmap(
                corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax,
                linewidths=0.5, linecolor="#2D3344", cbar_kws={"shrink": 0.8},
            )
            ax.set_title("Matriz de Correlación", color="#F1F5F9", fontsize=14)
            ax.tick_params(colors="#94A3B8")
            plt.tight_layout()
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            charts.append(("Correlación",
                           base64.b64encode(buf.getvalue()).decode()))
            plt.close(fig)

        # ── Distribution histograms ──
        numeric_cols = list(
            self.dm.df.select_dtypes(include=["number"]).columns[:6]
        )
        if numeric_cols:
            n = len(numeric_cols)
            ncols = min(3, n)
            nrows = (n + ncols - 1) // ncols
            fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
            fig.patch.set_facecolor("#0F1117")
            if n == 1:
                axes_flat = [axes]
            else:
                axes_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

            for i, col in enumerate(numeric_cols):
                ax = axes_flat[i]
                ax.set_facecolor("#0F1117")
                self.dm.df[col].dropna().hist(
                    bins=30, ax=ax, color="#6366F1", edgecolor="#0F1117", alpha=0.8,
                )
                ax.set_title(col, color="#F1F5F9", fontsize=11)
                ax.tick_params(colors="#94A3B8", labelsize=8)
                for spine in ax.spines.values():
                    spine.set_color("#2D3344")
            for i in range(len(numeric_cols), len(axes_flat)):
                axes_flat[i].set_visible(False)

            plt.tight_layout()
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            charts.append(("Distribuciones",
                           base64.b64encode(buf.getvalue()).decode()))
            plt.close(fig)

        # ── Build HTML ──
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        charts_html = ""
        for title, img_b64 in charts:
            charts_html += (
                f'<div class="chart-section"><h3>{title}</h3>'
                f'<img src="data:image/png;base64,{img_b64}" alt="{title}"></div>'
            )

        desc_html = (
            desc.to_html(classes="data-table", border=0)
            if not desc.empty
            else "<p>Sin columnas numéricas</p>"
        )
        missing_html = (
            missing.to_html(classes="data-table", border=0, index=False)
            if not missing.empty
            else ""
        )
        preview_html = self.dm.df.head(20).to_html(
            classes="data-table", border=0, index=False
        )

        file_name = info.get("file_name", "Dataset")
        rows = info.get("rows", 0)
        cols = info.get("cols", 0)
        memory = info.get("memory", "N/A")
        total_missing = int(missing["Faltantes"].sum()) if not missing.empty else 0

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte — {file_name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0F1117;color:#F1F5F9;padding:40px}}
.header{{text-align:center;margin-bottom:40px;padding:30px;background:linear-gradient(135deg,#1A1D27,#21252F);border-radius:16px;border:1px solid #2D3344}}
.header h1{{font-size:28px;background:linear-gradient(90deg,#6366F1,#22D3EE);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}}
.header p{{color:#94A3B8;font-size:14px}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}}
.metric{{background:#21252F;border:1px solid #2D3344;border-radius:12px;padding:20px;text-align:center}}
.metric .value{{font-size:32px;font-weight:700;color:#6366F1}}
.metric .label{{color:#94A3B8;font-size:13px;margin-top:4px}}
.section{{background:#21252F;border:1px solid #2D3344;border-radius:12px;padding:24px;margin-bottom:24px}}
.section h2{{font-size:18px;color:#F1F5F9;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #2D3344}}
.data-table{{width:100%;border-collapse:collapse;font-size:13px}}
.data-table th{{background:#1A1D27;color:#94A3B8;padding:10px 12px;text-align:left;font-weight:600;border-bottom:2px solid #6366F1}}
.data-table td{{padding:8px 12px;border-bottom:1px solid #2D3344;color:#CBD5E1}}
.data-table tr:hover td{{background:#2A2E3A}}
.chart-section{{margin:20px 0}}
.chart-section img{{max-width:100%;border-radius:8px}}
.footer{{text-align:center;color:#64748B;font-size:12px;margin-top:40px;padding-top:20px;border-top:1px solid #2D3344}}
</style>
</head>
<body>
<div class="header">
  <h1>📊 Reporte de Análisis de Datos</h1>
  <p>{file_name} — Generado el {now}</p>
</div>
<div class="metrics">
  <div class="metric"><div class="value">{rows:,}</div><div class="label">Filas</div></div>
  <div class="metric"><div class="value">{cols}</div><div class="label">Columnas</div></div>
  <div class="metric"><div class="value">{memory}</div><div class="label">Memoria</div></div>
  <div class="metric"><div class="value">{total_missing:,}</div><div class="label">Valores Faltantes</div></div>
</div>
<div class="section"><h2>📋 Vista Previa (primeras 20 filas)</h2>{preview_html}</div>
<div class="section"><h2>📈 Estadísticas Descriptivas</h2>{desc_html}</div>
<div class="section"><h2>❓ Valores Faltantes</h2>{missing_html}</div>
<div class="section"><h2>📉 Visualizaciones</h2>{charts_html}</div>
<div class="footer">Data Analyzer Pro — Reporte generado automáticamente</div>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return {"success": True, "path": path}
