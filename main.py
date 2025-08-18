from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth_app import router as auth_router
from cart_app import router as cart_router

app = FastAPI()

origins = [
    "https://brunopulheze.github.io",  # your deployed frontend
    "http://localhost:3000"              # local development (React default)
]

# Add CORS middleware to the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(cart_router)