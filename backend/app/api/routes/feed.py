# backend/app/api/routes/feed.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Paper, User
from app.ai.searcher import get_relevant_papers, get_papers_for_project
from app.ai.summarizer import summarize_feed_batch, summarize_paper_full

router = APIRouter()


# -------------------------------------------------------
# PERSONALIZED FEED — main feed for a user
# -------------------------------------------------------

@router.get("/{user_id}")
async def get_personalized_feed(
    user_id: str,
    db: Session = Depends(get_db)
):
    # fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check user has interests
    if not user.interests or len(user.interests) == 0:
        raise HTTPException(
            status_code=400,
            detail="User has no interests set. Please update profile first."
        )

    # get relevant papers via Qdrant semantic search
    papers = get_relevant_papers(
        interests=user.interests,
        db=db,
        top_k=20
    )

    if not papers:
        return {
            "user_id": user_id,
            "designation": user.designation,
            "skill_level": user.skill_level,
            "total": 0,
            "papers": []
        }

    # light summarize any unsummarized papers
    papers = summarize_feed_batch(
        papers=papers,
        designation=user.designation or "college student",
        skill_level=user.skill_level or "intermediate",
        db=db
    )

    # format response
    feed = []
    for paper in papers:
        feed.append({
            "id": str(paper.id),
            "title": paper.title,
            "authors": paper.authors,
            "field": paper.field,
            "published_date": str(paper.published_date) if paper.published_date else None,
            "source_url": paper.source_url,
            "summary_one_min": paper.summary_one_min,
            "difficulty_score": paper.difficulty_score,
            "suggested_stack": paper.suggested_stack,
            "estimated_build_time": paper.estimated_build_time,
        })

    return {
        "user_id": user_id,
        "designation": user.designation,
        "skill_level": user.skill_level,
        "total": len(feed),
        "papers": feed
    }


# -------------------------------------------------------
# PAPER DETAIL — full deep summary for one paper
# -------------------------------------------------------

@router.get("/{user_id}/paper/{paper_id}")
async def get_paper_detail(
    user_id: str,
    paper_id: str,
    db: Session = Depends(get_db)
):
    # fetch user for role context
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # fetch paper
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # full summarize if not done yet
    paper = summarize_paper_full(
        paper=paper,
        designation=user.designation or "college student",
        skill_level=user.skill_level or "intermediate",
        db=db
    )

    # find related papers for this paper's context
    related_papers = get_papers_for_project(
        project_description=f"{paper.title}. {paper.abstract}",
        db=db,
        top_k=5
    )

    # exclude the current paper from related
    related_papers = [p for p in related_papers if str(p.id) != paper_id]

    return {
        "id": str(paper.id),
        "title": paper.title,
        "authors": paper.authors,
        "field": paper.field,
        "published_date": str(paper.published_date) if paper.published_date else None,
        "source_url": paper.source_url,
        "abstract": paper.abstract,
        "summary_one_min": paper.summary_one_min,
        "summary_five_min": paper.summary_five_min,
        "summary_deep": paper.summary_deep,
        "build_ideas": paper.build_ideas,
        "suggested_stack": paper.suggested_stack,
        "difficulty_score": paper.difficulty_score,
        "estimated_build_time": paper.estimated_build_time,
        "related_papers": [
            {
                "id": str(rp.id),
                "title": rp.title,
                "field": rp.field,
                "summary_one_min": rp.summary_one_min,
                "difficulty_score": rp.difficulty_score,
            }
            for rp in related_papers
        ]
    }


# -------------------------------------------------------
# PROJECT DETAIL — related papers for a project context
# used when user is on a specific project page
# -------------------------------------------------------

@router.get("/{user_id}/project-papers")
async def get_papers_for_project_page(
    user_id: str,
    project_description: str,
    db: Session = Depends(get_db)
):
    """
    Called from project detail page.
    Pass project description as query param.
    Returns top 5 most relevant research papers.
    """

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    papers = get_papers_for_project(
        project_description=project_description,
        db=db,
        top_k=5
    )

    return {
        "project_description": project_description,
        "total": len(papers),
        "papers": [
            {
                "id": str(p.id),
                "title": p.title,
                "authors": p.authors,
                "field": p.field,
                "source_url": p.source_url,
                "summary_one_min": p.summary_one_min,
                "difficulty_score": p.difficulty_score,
            }
            for p in papers
        ]
    }