from fastapi import APIRouter
router=APIRouter()

@router.get("/history")
def history():
    return {"status":"scaffold","message":"Scan history endpoint"}
