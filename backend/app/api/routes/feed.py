from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def get_feed():
    return {"message": "feed route working"}