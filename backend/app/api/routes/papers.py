from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Paper
from app.ingestion.arxiv_fetcher import fetch_papers

router = APIRouter()

@router.get("/")
async def get_papers(db: Session = Depends(get_db)):
    papers = db.query(Paper).order_by(Paper.created_at.desc()).limit(50).all()
    return papers

@router.get("/fetch/{field}")
async def fetch_live(field: str):
    papers = await fetch_papers(field)
    return papers

@router.post("/ingest/{field}")
async def ingest_papers(field: str, db: Session = Depends(get_db)):
    papers_data = await fetch_papers(field, max_results=10)
    
    added = 0
    skipped = 0
    
    for p in papers_data:
        # Check for duplicate
        existing = db.query(Paper).filter(Paper.arxiv_id == p["arxiv_id"]).first()
        if existing:
            skipped += 1
            continue
        
        paper = Paper(
            arxiv_id=p["arxiv_id"],
            title=p["title"],
            authors=p["authors"],
            abstract=p["abstract"],
            source_url=p["source_url"],
            published_date=p.get("published_date"),
            field=field,
        )
        db.add(paper)
        added += 1
    
    db.commit()
    return {"field": field, "added": added, "skipped": skipped}

@router.get("/{paper_id}")
async def get_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper