from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_app import router as auth_router
from cart_app import router as cart_router

app = FastAPI()

# Add CORS middleware to the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(cart_router)