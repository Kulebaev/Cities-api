import http.server
from urllib.parse import unquote
import json

class GeoNamesHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path.startswith('/city'):
            parts = self.path.split('/')
            if len(parts) == 3:
                geonameid = parts[2]
                city_info = self.get_city_info(geonameid)
                self.wfile.write(json.dumps(city_info).encode())
            elif len(parts) == 5 and parts[2] == 'compare':
                city1 = parts[3]
                city2 = parts[4]
                comparison_info = self.compare_cities(city1, city2)
                self.wfile.write(json.dumps(comparison_info).encode())
        elif self.path.startswith('/cities'):
            page = int(self.get_query_param('page', 1))
            per_page = int(self.get_query_param('per_page', 5))
            cities = self.get_cities(page, per_page)
            self.wfile.write(json.dumps(cities).encode())
        elif self.path.startswith('/suggest'):
            partial_name = self.get_query_param('name', '')
            partial_name = unquote(partial_name)
            #print(partial_name)
            suggestions = self.get_city_name_suggestions(partial_name)
            self.wfile.write(json.dumps(suggestions).encode())

    def get_query_param(self, param_name, default_value):
        query = self.path.split('?')
        if len(query) > 1:
            params = query[1].split('&')
            for param in params:
                key, value = param.split('=')
                if key == param_name:
                    return value
        return default_value

    def get_city_info(self, geonameid):
        cities = self.parse_cities_file()  # Загрузка данных городов

        city_info = cities.get(geonameid, None)
    

        if city_info is not None:
            return {
                "geonameid": geonameid,
                "name": city_info["name"],
                "latitude": city_info["latitude"],
                "longitude": city_info["longitude"],
                "population": city_info["population"],
                "timezone": city_info["timezone"],
                "utc_offset": city_info["utc_offset"]
            }
        else:
            return {"error": "City not found"}


    def parse_cities_file(self):
        cities = {}

        with open("RU.txt", "r", encoding="utf-8") as file:
            for line in file:
                #print(repr(line))
                parts = line.strip().split(":")  # Разделитель ":"
                geonameid = parts[0]
                name = parts[1]
                latitude = parts[2]
                longitude = parts[3]
                population = parts[4]
                timezone = parts[5]
                utc_offset = parts[6]

                if name != "" and name.isalpha():
                    cities[geonameid] = {
                        "name": name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "population": population,
                        "timezone": timezone,
                        "utc_offset": utc_offset
                    }
        return cities



    def compare_cities(self, city1_name, city2_name):
        city1 = None
        city2 = None

        city1_name = unquote(city1_name)
        city2_name = unquote(city2_name)

        #print(unquote(city1_name), unquote(city2_name))

        cities_data = self.parse_cities_file()  # Загрузка данных городов

        for geonameid, city in cities_data.items():
            if city['name'] == city1_name:
                if city1 is None or city['population'] > city1['population']:
                    city1 = city
            elif city['name'] == city2_name:
                if city2 is None or city['population'] > city2['population']:
                    city2 = city

        if city1 is None:
            return f"Город {city1_name} не найден в базе данных."
        if city2 is None:
            return f"Город {city2_name} не найден в базе данных."

        if city1['latitude'] > city2['latitude']:
            northern_city = city1_name
        elif city1['latitude'] < city2['latitude']:
            northern_city = city2_name
        else:
            northern_city = "оба города на одной широте"

        if city1['timezone'] == city2['timezone']:
            timezone_match = "Временные зоны одинаковы."
        else:
            if city1['utc_offset'] > city2['utc_offset']:
                time_diff = int(city1['utc_offset']) - int(city2['utc_offset'])
            else:
                time_diff = int(city2['utc_offset']) - int(city1['utc_offset'])
            timezone_match = f"Временные зоны различаются. Разница во времени {time_diff} ч." 

        result = f"{city1_name} ({city1['population']} чел.) vs {city2_name} ({city2['population']} чел.). "
        result += f"Севернее: {northern_city}. {timezone_match}"

        return result

    def get_cities(self, page, per_page):
        cities_data = self.parse_cities_file()  # Загрузка данных городов

        # Определение начального и конечного индексов для выборки городов
        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        # Получение выборки городов для заданной страницы
        cities_on_page = list(cities_data.values())[start_index:end_index]

        cities_info = []
        for city in cities_on_page:
            cities_info.append({
                "name": city["name"],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "population": city["population"],
                "timezone": city["timezone"]
            })

        return cities_info

    def get_city_name_suggestions(self, partial_name):
        cities_data = self.parse_cities_file()  # Загрузка данных городов

        suggestions = []
        for geonameid, city in cities_data.items():
            if city['name'].lower().startswith(partial_name.lower()):
                suggestions.append(city['name'])
        
        return suggestions

def main():
    server_address = ('127.0.0.1', 8000)
    httpd = http.server.HTTPServer(server_address, GeoNamesHTTPRequestHandler)
    print('Starting server...')
    httpd.serve_forever()

if __name__ == '__main__':
    main()
