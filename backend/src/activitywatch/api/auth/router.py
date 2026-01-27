from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Работа с пользователями"])

router.post("/login")
async def login():
    pass

router.post("/register")
async def register():
    pass

router.post("/register_with_google")
async def register_with_google():
    pass

router.post("/logout")
async def logout():
    pass

router.post("/token")
async def create_api_token():
    pass