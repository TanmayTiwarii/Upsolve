from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", include_in_schema=False)
@router.head("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}
