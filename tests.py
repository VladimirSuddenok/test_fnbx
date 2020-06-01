from aiohttp import web
from main import Server
import pytest
import datetime
import time

def create_app(loop):
    return Server(loop=loop)

async def test_hello(test_client):
    client = await test_client(create_app)
    resp = await client.get("/hello_world")
    assert resp.status == 200
    text = await resp.text()
    assert text == "hello"

async def test_post_struct_error(test_client):
    client = await test_client(create_app)
    #check 'get json'
    resp = await client.post("/visited_links", 
                             data="123")
    assert resp.status == 400
    #check 'get links'
    resp = await client.post("/visited_links", 
                             data='{"abc":"abc"}')
    assert resp.status == 400
    #check 'is strings'
    resp = await client.post("/visited_links", 
                             data='{"links":[1, "key2", "key3"]}')
    assert resp.status == 400

async def test_post_link_error(test_client):
    client = await test_client(create_app)
    #check 'is link'
    data  = '{"links": ["abc", "ya.ru", "asd", "asdasd"]}'
    resp = await client.post("/visited_links", 
                             data=data)
    assert resp.status == 400
    text = await resp.text()
    print(text)
    check = 'following data' in text
    assert check == True

async def test_post_save_links(test_client):
    client = await test_client(create_app)
    #correct save data
    data = ('{"links": ["https://ya.ru",' + \
            '"https://ya.ru?q=123","funbox.ru",' + \
            '"https://stackoverflow.com/questions/' + \
            '11828270/how-to-exit-the-vim-editor"]}')

    resp = await client.post("/visited_links", 
                             data=data)

    assert resp.status == 200
    text = await resp.text()
    print(text)
    check = 'ok' in text
    assert check == True

async def test_get_links_get_param_error(test_client):
    client = await test_client(create_app)
    #check correct get params
    url = "/visited_links?from_d=1545221231&to_d=1545217638"
    resp = await client.get(url)
    assert resp.status == 400

    text = await resp.text()
    print(text)
    check = 'required' in text
    assert check == True

async def test_get_links_success(test_client):
    client = await test_client(create_app)
    #correct save data
    data = ('{"links": ["https://ya.ru",' + \
            '"https://ya.ru?q=123","funbox.ru",' + \
            '"https://stackoverflow.com/questions/' + \
            '11828270/how-to-exit-the-vim-editor"]}')

    resp = await client.post("/visited_links", 
                             data=data)

    assert resp.status == 200
    text = await resp.text()
    print(text)
    check = 'ok' in text
    assert check == True

    #checka get domains
    date_from = await get_time_stamp('tomorrow')
    date_to = await get_time_stamp('yesterday')

    url = f"/visited_links?from={date_from}&to={date_to}"
    print ('tyt', url)
    resp = await client.get(url)
    assert resp.status == 200
    text = await resp.text()
    print(text)
    
    check = 'ya.ru' in text
    assert check == True

async def get_time_stamp(when):
    dt = datetime.datetime.now()
    if when == 'tomorrow':
        dt = dt + datetime.timedelta(days=1)
    elif when == 'yesterday':
        dt = dt - datetime.timedelta(days=1)
    stamp = time.mktime(dt.timetuple())
    return str(int(stamp))