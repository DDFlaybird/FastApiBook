from typing import List, Optional, Set
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl
from fastapi import FastAPI, Query, Path, Body, Cookie

app = FastAPI()

# Query 对查询参数进行定义
# Path 对路径参数进行定义
# Body 对请求体参数进行定义，将单个参数嵌入请求体中，
# 对单个请求体的参数校验等
# Field 对请求体body参数进行原信息进行校验等
# Field和Body不同的是Field主要是对BaseModel子类
# 进行元信息定义，字段校验。

class Offer(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    items: List[Item]

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

@app.get('/')
async def root():
    return {
        "code": 200,
        "data": "fuck you django",
        "msg":""
    }

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
    return fake_items_db[skip : skip + limit]

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


    tax: Optional[float] = None

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
    d: str = Query(...,min_length=3),
    f:Optional[List[str]] = Query(["foo", "bar"])
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


@app.put("/items/{item_id}")
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

@app.post("/offers/")
async def create_offer(offer: Offer):
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

if __name__ == '__main__':
    pass