from aiohttp import web
import re
import redis
from typing import Tuple, Iterable, Union, Set

import datetime
import time

import os
#REDIS_HOST = os.environ['REDIS_HOST']
#REDIS_PORT = os.environ['REDIS_PORT']

class Server(web.Application):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        #database
        self._connection = redis.Redis(host='localhost',#REDIS_HOST, 
                                       port=6379,#REDIS_PORT,
                                       db=0)
        self._connection.flushdb()
        #urls
        self._basic_navigation()
        #urls pattern for reg
        self._pattern_link = r'^(https?:\/\/)?(\w{2,}\.\w+)(\.\w+)?'

    def _basic_navigation(self) -> None:
        self.add_routes([
            web.get("/hello_world", self._hello),

            web.post("/visited_links", self._post_visited_links),
            web.get("/visited_links", self._get_visited_links)])

    async def _get_visited_links(self, request) -> web.json_response:
        date_from = request.rel_url.query.get('from', False)
        date_to = request.rel_url.query.get('to', False)
        #check required params  
        if not date_from or not date_to:
            error, status = await self._struct_error_get(type = "required")
            return web.json_response(data={'status': error}, status=status)

        #check data content
        if not date_from.isdigit() or not date_to.isdigit():
            error, status = await self._struct_error_get(type = "digit")
            return web.json_response(data={'status': error}, status=status)

        result = await self._get_links(int(date_from), int(date_to))
        response = {"domains": [link.decode('utf-8') for link in result],
                    "status": "ok" }

        print ('response:', response)

        return web.json_response(data=response, status=200)
    
    async def _get_links(self, date_from: int, date_to: int) -> Set:
        keys = self._connection.keys()

        result = set()
        for key in keys:
            date = int(key)
            if date_from > date and date > date_to:
                data = self._connection.smembers(date)
                result = result.union(data)
            else:
                continue
        
        return result

    async def _struct_error_get(self, type: str) -> Tuple[str, str]:
        example = "/visited_links?from=1545221231&to=1545217638"
        if type == "required":
            error = f"required get-parameters: {example}"
        elif type == "digit":
            error = f"required get-parameters must be numbers: {example}"
        
        return error, 400

    async def _post_visited_links(self, request) -> web.json_response:
        #get json data
        try:
            data = await request.json()
        except Exception as ex:
            error, status = await self._struct_error_post()
            return web.json_response(data={'status':error}, status=status)

        #check data struct
        if not await self._check_data_struct(data):
            error, status = await self._struct_error_post()
            return web.json_response(data={'status':error}, status=status)
        
        #check data content
        status, data = await self._check_links(data['links'])
        if not status:
            status = 400
            data = str(data)
            error = f'following data is not a links: {data}'
            return web.json_response(data={'status':error}, status=status)

        #save data
        status = await self._save_data(data)
        if not status:
            status = 500
            error = 'save data error'
            return web.json_response(data={'status':error}, status=status)

        return web.json_response(data={"status": "ok"})
    
    async def _save_data(self, links: dict) -> bool:
        try:
            time = await self._get_timestamp()
            self._connection.sadd(time, *links)
            print (self._connection.sscan(time))
            return True
        except Exception as ex:
            return False
            
    async def _get_timestamp(self) -> str:
        dt = datetime.datetime.now()
        stamp = time.mktime(dt.timetuple())
        return str(int(stamp))

    async def _struct_error_post(self) -> Tuple[str, str]:
        example = '{"links": ["key1", "key2", "key3"]}'
        text = f"invalid data struct, expected: {example}"
        return text, 400
    
    async def _check_data_struct(self, data: dict) -> bool:
        try:
            links = data.get('links', False)
            if not links:
                return False
            if not await self._is_strings(links):
                return False

            return True
        except Exception as ex:
            return False

    async def _is_strings(self, data: list) -> bool:
        results = [isinstance(string, str) for string in data]
        if False in results:
            return False
        else:
            return True
        
    async def _check_links(self, raw_links: list) -> Tuple[bool, Iterable[str]]:
        #buffers
        links = set()
        incorrect_data = list()
        #link proccessing
        for link in raw_links:
            result = await self._is_link(link)
            if result:
                links.add(result)
            else:
                incorrect_data.append(link)

        if incorrect_data:
            return False, incorrect_data
        else:
            return True, links
            
    async def _is_link(self, link: str) -> Union[str, bool]:
        result = re.match(self._pattern_link, link)
        if result:
            return result.group(2) + result.group(3) if result.group(3) \
                   else result.group(2)
        else:
            return False
        
    async def _hello(self, request) -> web.Response:
        return web.Response(text="hello")

if __name__ == "__main__":
    web.run_app(Server())