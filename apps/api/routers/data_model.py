"""Endpoints pour le module Data Model."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.db import get_db
from models.analysis import Analysis
from services.data_model.reference import (
    BRAZE_DATA_MODEL,
    get_all_entity_names,
    get_entity,
    get_entities_by_category,
    get_full_hierarchy_mermaid,
    build_hierarchy,
)
from services.data_model.analyzer import (
    analyze_use_cases,
    analyze_use_cases_demo,
)
from services.data_model.exporter import export_to_excel, export_to_csv
from services.data_model.estimator import estimate_data_points

router = APIRouter(prefix="/api/data-model", tags=["data-model"])


class AnalyzeRequest(BaseModel):
    use_cases: list[str]
    project_name: str | None = None
    project_id: str | None = None
    model: str | None = None
    demo: bool = False


class EstimateDataPointsRequest(BaseModel):
    analysis_id: str | None = None
    analysis_result: dict | None = None
    user_volume: int = 100000
    update_frequencies: dict | None = None


@router.post("/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    """Analyser un ou plusieurs use cases et retourner les entites Braze requises."""
    if req.demo:
        result = analyze_use_cases_demo()
    else:
        result = analyze_use_cases(req.use_cases, model=req.model)

    # Persister en BDD
    analysis = Analysis(
        project_id=req.project_id,
        project_name=req.project_name,
        use_case="\n".join(req.use_cases),
        result=result,
        model_used=req.model or "demo",
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return {
        "id": analysis.id,
        "result": result,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


@router.get("/entities")
def list_entities(category: str | None = None):
    """Liste des entites Braze (optionnellement filtrees par categorie)."""
    if category:
        names = get_entities_by_category(category)
    else:
        names = get_all_entity_names()

    return [
        {"name": name, **BRAZE_DATA_MODEL[name]}
        for name in names
    ]


@router.get("/entities/{name}")
def get_entity_detail(name: str):
    """Detail d'une entite Braze specifique."""
    entity = get_entity(name)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entite '{name}' non trouvee")
    return {"name": name, **entity}


@router.get("/hierarchy")
def get_hierarchy():
    """Diagramme Mermaid et arbre hierarchique du data model complet."""
    return {
        "mermaid": get_full_hierarchy_mermaid(),
        "tree": build_hierarchy(),
    }


@router.get("/history")
def get_history(db: Session = Depends(get_db), limit: int = 50):
    """Historique des analyses (BDD)."""
    analyses = (
        db.query(Analysis)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": a.id,
            "project_id": a.project_id,
            "project_name": a.project_name,
            "use_case": a.use_case,
            "model_used": a.model_used,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]


@router.get("/history/{analysis_id}")
def get_analysis_detail(analysis_id: str, db: Session = Depends(get_db)):
    """Detail d'une analyse passee."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvee")
    return {
        "id": analysis.id,
        "project_id": analysis.project_id,
        "project_name": analysis.project_name,
        "use_case": analysis.use_case,
        "result": analysis.result,
        "model_used": analysis.model_used,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


@router.get("/export/{analysis_id}")
def export_analysis(
    analysis_id: str,
    format: str = Query("excel", pattern="^(excel|csv)$"),
    db: Session = Depends(get_db),
):
    """Exporte une analyse en Excel ou CSV."""
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analyse '{analysis_id}' non trouvee")

    result_data = analysis.result
    if not result_data:
        raise HTTPException(status_code=400, detail="Aucun resultat a exporter pour cette analyse")

    project = analysis.project_name or "braze_data_model"
    safe_name = project.replace(" ", "_").replace("/", "_")

    if format == "excel":
        content = export_to_excel(result_data)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.xlsx"',
            },
        )
    else:
        content = export_to_csv(result_data)
        return Response(
            content=content.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}.csv"',
            },
        )


@router.post("/estimate-data-points")
def estimate_dp(req: EstimateDataPointsRequest, db: Session = Depends(get_db)):
    """Estime la consommation de data points Braze pour une analyse donnee."""
    # Recuperer le resultat d'analyse
    analysis_result = req.analysis_result

    if not analysis_result and req.analysis_id:
        analysis = db.query(Analysis).filter(Analysis.id == req.analysis_id).first()
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analyse '{req.analysis_id}' non trouvee",
            )
        analysis_result = analysis.result

    if not analysis_result:
        raise HTTPException(
            status_code=400,
            detail="Fournissez soit 'analysis_id' soit 'analysis_result'",
        )

    if req.user_volume < 1:
        raise HTTPException(
            status_code=400,
            detail="user_volume doit etre superieur a 0",
        )

    return estimate_data_points(
        analysis_result=analysis_result,
        user_volume=req.user_volume,
        update_frequency=req.update_frequencies,
    )
