from datetime import datetime, timezone

TOPICS = [
    "popular music new songs", "gaming highlights", "viral food videos",
    "football and sports highlights", "new technology and AI",
    "movie trailers and entertainment", "travel destinations",
    "funny comedy clips", "cute animals", "fitness and workout videos",
]
week = int(datetime.now(timezone.utc).strftime("%V"))
print(TOPICS[week % len(TOPICS)])
