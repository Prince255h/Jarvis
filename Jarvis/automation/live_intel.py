import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import datetime

class LiveIntel:
    @staticmethod
    def get_time_and_date():
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")
        return f"The current time is {time_str}, on {date_str}, sir."

    @staticmethod
    def get_weather(city=None):
        try:
            if city:
                encoded = urllib.parse.quote(city)
                url = f"https://wttr.in/{encoded}?format=j1"
            else:
                url = "https://wttr.in/?format=j1"
                
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            current = data['current_condition'][0]
            temp_c = current['temp_C']
            feels_like = current['FeelsLikeC']
            desc = current['weatherDesc'][0]['value']
            humidity = current['humidity']
            wind = current['windspeedKmph']
            
            loc = city.capitalize() if city else "your current location"
            return (
                f"Weather report for {loc}: The temperature is {temp_c} degrees Celsius, "
                f"feeling like {feels_like} degrees with {desc.lower()}. Humidity is at {humidity} percent "
                f"and wind speed is {wind} kilometers per hour, sir."
            )
        except Exception as e:
            return f"Unable to fetch weather telemetry at this moment: {e}"

    @staticmethod
    def get_top_news(count=3):
        try:
            url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as response:
                content = response.read()
                
            root = ET.fromstring(content)
            items = root.findall('.//item')[:count]
            
            if not items:
                return "No news headlines were retrieved, sir."
                
            headlines = []
            for i, item in enumerate(items, 1):
                title = item.find('title').text
                # Clean publisher from title if format is "Title - Publisher"
                if " - " in title:
                    title = title.split(" - ")[0]
                headlines.append(f"Headline {i}: {title}.")
                
            return f"Here are today's top stories, sir. " + " ".join(headlines)
        except Exception as e:
            return f"Unable to retrieve live news feed: {e}"

    @staticmethod
    def get_joke():
        try:
            url = "https://official-joke-api.appspot.com/random_joke"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
            return f"{data['setup']} ... {data['punchline']}"
        except Exception:
            return "Why do programmers prefer dark mode? Because light attracts bugs, sir."

    @staticmethod
    def get_advice():
        try:
            url = "https://api.adviceslip.com/advice"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
            return f"A piece of advice, sir: {data['slip']['advice']}"
        except Exception:
            return "Always keep your system updated and your coffee warm, sir."
