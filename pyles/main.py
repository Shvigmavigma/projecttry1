from pydantic import BaseModel, Field, EmailStr, ConfigDict
from fastapi import FastAPI


app = FastAPI()





data={
    "email" : "abd@mail.ru",
    "bio" : None,
    "age" : 12,
}
data_wo_age={
    "email" : "abd@mail.ru",
    "bio" : None,

}

class UserSchema(BaseModel):
    email : EmailStr
    bio : str | None = Field(max_length=10000)

    model_config=ConfigDict(extra='forbid')
 
users=[]   
    
@app.post(path="/users", summary="User_add", tags=["Userwork"])
def add_user(user : UserSchema):
    users.append(user)
    return{ "ok" : True, "msg" : "User added"}

@app.get(path="/users", summary="User_add", tags=["Userwork"])
def add_user() -> list[UserSchema]:
    return users
    
class User_w_age(UserSchema):
    age : int = Field(ge=0, le=130)
    