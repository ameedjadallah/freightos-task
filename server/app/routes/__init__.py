from fastapi import APIRouter
from .upload import router as upload_router
from .compare import router as compare_router

router = APIRouter()

router.include_router(upload_router, prefix="/upload", tags=["Upload"])
router.include_router(compare_router, prefix="/compare", tags=["Comparison"])
