#!/usr/bin/env python3
"""Create a private test playlist from up to five YouTube search results."""
import json, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
API="https://www.googleapis.com/youtube/v3"
def call(url, token, method="GET", body=None):
    data=None if body is None else json.dumps(body).encode()
    headers={"Authorization":"Bearer "+token,"Accept":"application/json"}
    if data is not None: headers["Content-Type"]="application/json"
    req=urllib.request.Request(url,data=data,method=method,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8",errors="replace")
        raise RuntimeError(f"API error {e.code}: {detail[:900]}") from None
def main():
    missing=[k for k in ("YOUTUBE_CLIENT_ID","YOUTUBE_CLIENT_SECRET","YOUTUBE_REFRESH_TOKEN") if not os.getenv(k)]
    if missing: raise RuntimeError("Missing secrets: "+", ".join(missing))
    form=urllib.parse.urlencode({"client_id":os.environ["YOUTUBE_CLIENT_ID"],"client_secret":os.environ["YOUTUBE_CLIENT_SECRET"],"refresh_token":os.environ["YOUTUBE_REFRESH_TOKEN"],"grant_type":"refresh_token"}).encode()
    req=urllib.request.Request("https://oauth2.googleapis.com/token",data=form,headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: token=json.loads(r.read().decode())["access_token"]
    except urllib.error.HTTPError as e: raise RuntimeError("Google OAuth refresh failed: "+e.read().decode()[:900]) from None
    query=os.getenv("SEARCH_QUERY","popular music 2026").strip()
    title=os.getenv("PLAYLIST_TITLE","Automation Test - Private Playlist").strip()
    count=max(1,min(5,int(os.getenv("MAX_RESULTS","5"))))
    after=(datetime.now(timezone.utc)-timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params=urllib.parse.urlencode({"part":"snippet","type":"video","q":query,"maxResults":count,"order":"viewCount","safeSearch":"moderate","publishedAfter":after})
    found=call(API+"/search?"+params,token).get("items",[])
    if not found:
        params=urllib.parse.urlencode({"part":"snippet","type":"video","q":query,"maxResults":count,"order":"viewCount","safeSearch":"moderate"})
        found=call(API+"/search?"+params,token).get("items",[])
    ids=list(dict.fromkeys(i.get("id",{}).get("videoId") for i in found if i.get("id",{}).get("videoId")))
    if not ids: raise RuntimeError("No candidate videos found; no playlist created.")
    pl=call(API+"/playlists?part=snippet,status",token,"POST",{"snippet":{"title":title,"description":"Private automation proof of concept. Topic: "+query},"status":{"privacyStatus":"private"}})
    added=[]
    for vid in ids:
        try:
            call(API+"/playlistItems?part=snippet",token,"POST",{"snippet":{"playlistId":pl["id"],"resourceId":{"kind":"youtube#video","videoId":vid}}})
            added.append(vid)
        except RuntimeError as e: print("Skipped video",vid,str(e))
    url="https://www.youtube.com/playlist?list="+pl["id"]
    with open("playlist-test-result.txt","w",encoding="utf-8") as f:
        f.write(f"Title: {title}\nPrivacy: private\nTopic: {query}\nURL: {url}\nVideos added: {len(added)} of {len(ids)}\n")
        f.write("\n".join("https://www.youtube.com/watch?v="+v for v in added)+"\n")
    print("Private playlist created:",url)
    print(f"Videos added: {len(added)} of {len(ids)}")
if __name__=="__main__":
    try: main()
    except Exception as e:
        print("ERROR:",e)
        with open("playlist-test-result.txt","w",encoding="utf-8") as f: f.write("FAILED\n"+str(e)+"\n")
        raise
