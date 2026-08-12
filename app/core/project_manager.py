"""Project structure manager for Data Analyzer Pro."""
from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any


class ProjectManager:
    """Creates, saves and loads Data Analyzer Pro projects."""

    @staticmethod
    def create_project(project_path: str | Path) -> Path:
        path = Path(project_path)
        folders = [
            "datasets",
            "raw",
            "cleaned",
            "transformations",
            "analytics",
            "visualizations",
            "exports",
            "history",
            "config",
        ]
        for folder in folders:
            (path / folder).mkdir(parents=True, exist_ok=True)
        manifest = path / "project.json"
        if not manifest.exists():
            manifest.write_text(
                json.dumps(
                    {
                        "name": path.name,
                        "created_at": datetime.now().isoformat(timespec="seconds"),
                        "updated_at": datetime.now().isoformat(timespec="seconds"),
                        "version": 1,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        return path

    @staticmethod
    def save_project(project_path: str | Path, data_manager: Any, settings: dict[str, Any] | None = None) -> Path:
        path = ProjectManager.create_project(project_path)
        state_path = path / "project_state.pkl"
        payload = {
            "file_name": data_manager.file_name,
            "file_path": data_manager.file_path,
            "current_dataframe": data_manager.df,
            "original_dataframe": data_manager.original_df,
            "datasets": data_manager.datasets,
            "history": data_manager.history.entries(),
            "analysis_sessions": data_manager.analysis_sessions,
            "charts": data_manager.created_charts,
            "settings": settings or {},
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        with open(state_path, "wb") as handle:
            pickle.dump(payload, handle)
        manifest = {
            "name": path.name,
            "updated_at": payload["saved_at"],
            "dataset": data_manager.file_name,
            "datasets": len(data_manager.datasets),
            "version": 1,
        }
        (path / "project.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return state_path

    @staticmethod
    def load_project(project_path: str | Path, data_manager: Any) -> dict[str, Any]:
        path = Path(project_path)
        state_path = path / "project_state.pkl"
        if not state_path.exists():
            raise FileNotFoundError("El proyecto no contiene project_state.pkl")
        with open(state_path, "rb") as handle:
            payload = pickle.load(handle)
        data_manager.df = payload.get("current_dataframe")
        data_manager.original_df = payload.get("original_dataframe")
        data_manager.file_name = payload.get("file_name")
        data_manager.file_path = payload.get("file_path")
        data_manager.datasets = payload.get("datasets", {})
        data_manager.analysis_sessions = payload.get("analysis_sessions", [])
        data_manager.created_charts = payload.get("charts", [])
        data_manager.current_project = str(path)
        
        history_entries = payload.get("history", [])
        data_manager.history.clear()
        for entry in history_entries:
            data_manager.history._past.append(entry)
            
        if data_manager.df is not None:
            from app.core.ohlc_detector import detect_ohlc

            data_manager.ohlc_metadata = detect_ohlc(data_manager.df)
        data_manager.notify()
        return payload

