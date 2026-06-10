import requests

urls = [
    'https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6xFvP7FVvGjBmanNPa3pVtUoUYYYZqeobIwIsO1lMGz6_HYLefJ239zyadQHNRzsrjubzfXZv6oLRnMMRL6_x-l9ldyFq71iK3JARCsxZQ_Y-oOAvE9ZiBUxGimee3EH_2GkeebQLfj1dhtq4GUegT-KrZmUaDZ9WjTZZzcQKC_9LQ2_7xZymxH_1',
    'https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF6L5Hfi4EdL3DRB0RTCQFGVerEz_Q6fCwqBCS1DkiuzleVIw8bCyC3C3ZB2E118EJLnHy9hsAbR0H1F-n_CuY-juvZsA6Hq-IZhFUtMrlTaTtrBzLkDXI5FmwYwHQi5yHzRQoLOT4kJD4b6ZJJdQ5F6rQgTdC76nb-jQvSG8lHyxjhBvw4rHil8tOyLT6C'
]

for i, url in enumerate(urls):
    try:
        r = requests.head(url, allow_redirects=True, timeout=15)
        print(f"URL {i+1} redirected to: {r.url}")
    except Exception as e:
        print(f"Error for URL {i+1}: {e}")
