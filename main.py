from enum import Enum
from typing import List, Optional, Set

from fastapi import FastAPI, Query, Path, Body, Cookie, Header, Form, UploadFile, File, HTTPException, Request, Depends, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, HttpUrl
from starlette.exceptions import HTTPException as StarletteHTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)

# Query 对查询参数进行定义
# Path 对路径参数进行定义
# Body 对请求体参数进行定义，将单个参数嵌入请求体中，
# 对单个请求体的参数校验等
# Field 对请求体body参数进行原信息进行校验等
# Field和Body不同的是Field主要是对BaseModel子类
# 进行元信息定义，字段校验。


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


# 使用pydanic中的basemodel来定义请求体
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


# 使用Field对请求体中的参数校验
class Item2(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


# Optional 和 dict 都可以在docs页面展示出来
# 嵌套的basemodel类型，list不显示但是可以正常传参
# Set就不可以传递了
class Item3(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: Set[int] = set()
    image: List[Image] = []


class Item4(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None
    tags: Set[str] = set()
    images: Optional[List[Image]] = None


class CustomItem(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            }
        }


class ItemPublic(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: float = 10.5


class Offer(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    items: List[Item]


@app.get('/')
async def root():
    return {
        "code": 200,
        "data": "fuck you django",
        "msg": ""
    }


@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


# ! 特殊的一种模式，在参数：path声名这个参数是一个path路径
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


# 查询参数
fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip + limit]


# item_id 是路径参数，qw
# shor是一个可选查询参数 可输入1/0; true/flase ;on/off; yes/no
@app.get("/item_info/{item_id}")
async def read_item_o(item_id: str, q: Optional[str] = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
        user_id: int, item_id: str, q: Optional[str] = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


# item_id 是一个路径参数
# needy是一个必须的查询参数
# 给needy一个默认值就将其变成一个可选查询参数
@app.get("/read_item/{item_id}")
async def read_user_item(item_id: str, needy: str, txt: str = None, a: Optional[str] = 0):
    item = {"item_id": item_id, "needy": needy}
    return item


# 直接对Item对象操作
@app.post("/items/")
async def create_item(item: Item):
    return item


# 使用Query函数限定查询参数 q 长度为50
# 此时Query函数将显示的声名 q 参数为可选参数
# 使用regex可以给字段条件正则条件regex="^fixedquery$"
# 使用None作为Query第一个参数可以当作将参数标记为可选参数
# 使用...可以将其作为一个必选参数，当然...是一种简单的写法
# 只要我们给Query第一参数给非None的参数，就可以将其标记为必选参数
# query参数deprecated表示参数已经被废弃
@app.get("/limit_items/")
async def read_items(
        q: Optional[str] = Query(
            None,
            min_length=3,
            max_length=50,
            title="Query string",
            description="Query string for the items to search in the database that have a good match",
            alias="item-query"
        ),
        d: str = Query(..., min_length=3),
        f: Optional[List[str]] = Query(["foo", "bar"])
):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@app.get("/paths/{item_id}")
async def read_path(
        item_id: int = Path(..., title="The ID of the item to get"),
        q: Optional[str] = Query(None, alias="item-query"),
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


class User(BaseModel):
    username: str
    full_name: Optional[str] = None


@app.put("/items_emed/{item_id}")
async def update_item(
        *,
        item_id: int,
        item: Item2,
        user: User,
        importance: int = Body(..., gt=0),
        q: Optional[str] = None
):
    results = {"item_id": item_id, "item": item, "user": user, "importance": importance}
    if q:
        results.update({"q": q})
    return results


@app.put("/items_u/{item_id}")
async def update_item_u(item_id: int, item: Item3):
    results = {"item_id": item_id, "item": item}
    return results

# Body 嵌入单个请求体
@app.post("/offers/")
async def create_offer(offer: Offer = Body(..., embed=True)):
    return offer


@app.post("/images/multiple/")
async def create_multiple_images(images: List[Image]):
    return images


@app.put("/items_custom/{item_id}")
async def update_item_custom(item_id: int, item: CustomItem):
    results = {"item_id": item_id, "item": item}
    return results


@app.get("/items_cookies/")
async def read_items_cookies(ads_id: Optional[str] = Cookie(None)):
    return {"ads_id": ads_id}


@app.get("/items_header/")
async def read_items_header(user_agent: Optional[str] = Header(None, convert_underscores=False),
                            x_toker: Optional[List[str]] = Header(None, convert_underscores=False)):
    return {"User-Agent": user_agent, "x_token": x_toker}


items_public = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The Bar fighters", "price": 62, "tax": 20.2},
    "baz": {
        "name": "Baz",
        "description": "There goes my baz",
        "price": 50.2,
        "tax": 10.5,
    },
}


# response_model_include 返回体中包含的字段
# response_model_exclude 返回体中不包含的字段
@app.get("/items/{item_id}/public", response_model=ItemPublic, response_model_exclude={"tax"})
async def read_item_public_data(item_id: str):
    return items_public[item_id]


@app.post("/files/")
async def create_file(file: bytes = File(...)):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: List[UploadFile] = File(...)):
    return {"filename": file.filename}

# form 和 File是可以一起使用的
# body但是body不可以声名
# 因为form和body的content-type不同
@app.post("/files_fiel_form/")
async def create_file_form_filed(
        file: bytes = File(...), fileb: UploadFile = File(...), token: str = Form(...),
        where: Optional[str] = Query(None)
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }

items_errors = {"foo": "The Foo Wrestlers"}

@app.get("/items_error/{item_id}")
async def read_item(item_id: str):
    if item_id not in items_errors:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items_errors[item_id]}

@app.get("/items_custom_error/{item_id}")
async def read_item_custom(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")
    return {"item_id": item_id}

@app.get("/unicorns/{name}",
         summary="testing")
async def read_unicorn(name: str):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}

async def common_parameters(q: Optional[str] = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items_depends")
async def read_items_depend(commons: dict = Depends(common_parameters)):
    return commons

@app.get("/users_depends/")
async def read_users_depends(commons: dict = Depends(common_parameters)):
    return commons


class CommonQueryParams:
    def __init__(self, q: Optional[str] = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/class_depends/")
async def class_depends(commons: CommonQueryParams = Depends(CommonQueryParams)):
    response = {}
    if commons.q:
        response.update({"q": commons.q})
    items = fake_items_db[commons.skip : commons.skip + commons.limit]
    response.update({"items": items})
    return response


def query_extractor(q: Optional[str] = None):
    return q


def query_or_cookie_extractor(
    q: str = Depends(query_extractor), last_query: Optional[str] = Cookie(None)
):
    if not q:
        return last_query
    return q

class DBSession:
    def __init__(self):
        pass
    def close(self):
        print("close")
def do_something():
    raise ValueError('value_error')
# 依赖内部的错误可以在依赖内部捕捉，处理 但是yield必须返回一个对象
async def get_db():
    db = DBSession()
    try:
        do_something()
        yield db
    except ValueError as ee:
        raise HTTPException(status_code=404, detail={"msg": "down"})
    finally:
        db.close()
@app.get("/yield_error")
async def yield_error(get_db: DBSession = Depends(get_db)):
    print(get_db.status)
    return {"msg":"fuck"}
@app.get("/sub_depends_items/")
async def read_query(query_or_default: str = Depends(query_or_cookie_extractor)):
    return {"q_or_cookie": query_or_default}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/oauth2/")
async def read_items_oauth2(token: str = Depends(oauth2_scheme)):
    return {"token": token}

class OauthUser(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(OauthUser):
    hashed_password: str

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_hash_password(password: str):
    return "fakehashed" + password

def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


if __name__ == '__main__':
    pass
