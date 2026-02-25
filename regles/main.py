from fastapi import FastAPI, HTTPException, Response, Depends
from authx import AuthXConfig, AuthX
from pydantic import BaseModel

app = FastAPI()

config= AuthXConfig()


config.JWT_SECRET_KEY="SECTER_KEY"
config.JWT_ACCESS_COOKIE_NAME="my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]


securite = AuthX(config=config)


class UserLoginSchema(BaseModel):
    username: str
    password : str

@app.post("/login")
def login(creds: UserLoginSchema, response: Response):
    if creds.username == "test" and creds.password == "test":
        token = securite.create_access_token(uid="12345")
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        return{"access_token":token}
    raise HTTPException(status_code=401, detail="sosi")
    
    
@app.get("/protected", dependencies=[Depends(securite.access_token_required)])
def protected():
    return {"data" : "TOP SECRET"}