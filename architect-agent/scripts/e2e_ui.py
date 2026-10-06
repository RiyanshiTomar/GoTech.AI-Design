import json, re, requests, time
from playwright.sync_api import sync_playwright
API="http://localhost:8000"; OUT="/mnt/user-data/outputs/e2e"
P=["Create a 20m × 30m house with 3 bedrooms, a living room, kitchen and 2 bathrooms.","Make Bedroom 1 one meter wider.","Move the kitchen beside the living room."]
def rooms(pid):
    m=requests.get(f"{API}/api/projects/{pid}/model").json()
    return {r["id"]:(r["x"],r["y"],r["width"],r["depth"]) for f in m["floors"] for r in f["rooms"]}
def svg_rect(page,rid):
    return page.evaluate("""id=>{const g=document.querySelector('#room-'+id+' rect');return g?[+g.getAttribute('x'),+g.getAttribute('y'),+g.getAttribute('width'),+g.getAttribute('height')]:null}""",rid)
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=swiftshader","--enable-webgl","--ignore-gpu-blocklist"])
    pg=b.new_context(viewport={"width":1440,"height":900}).new_page()
    reqs=[]; pg.on("request",lambda r:reqs.append((r.method,r.url)) if "/api/" in r.url else None)
    errs=[]; pg.on("console",lambda m:errs.append(m.text) if m.type=="error" and "font" not in m.text.lower() else None)
    pg.goto("http://localhost:3000/design"); pg.wait_for_timeout(2500)
    pid=pg.evaluate("localStorage.getItem('gotec.project_id')"); print("project id:",pid)
    pg.screenshot(path=f"{OUT}/0_empty.png")
    snaps=[]; phases=set()
    for n,prompt in enumerate(P,1):
        pg.fill("textarea",prompt); pg.keyboard.press("Enter")
        t0=time.time()
        while time.time()-t0<90:
            chip=pg.locator("aside span.rounded-full").first.inner_text()
            phases.add(chip)
            if chip in("Valid",) or "error" in chip.lower(): 
                if time.time()-t0>1.5: break
            pg.wait_for_timeout(120)
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{OUT}/{n}_2d.png")
        r=rooms(pid); s={k:svg_rect(pg,k) for k in r}
        snaps.append((r,s)); print(f"after prompt {n}: chip={chip!r}, rooms={len(r)}")
        pg.click("button:has-text('3D model')"); pg.wait_for_timeout(4000); pg.screenshot(path=f"{OUT}/{n}_3d.png"); pg.click("button:has-text('2D plan')"); pg.wait_for_timeout(500)
    print("phases seen in UI chip:",sorted(phases))
    print("project id unchanged:",pg.evaluate("localStorage.getItem('gotec.project_id')")==pid)
    posts=[u for m,u in reqs if m=="POST"]; print("POSTs:",posts)
    print("creates:",sum(1 for u in posts if u.endswith("/api/projects")))
    print("glb fetches:",sum(1 for m,u in reqs if u.endswith("building.glb") or ".glb?" in u))
    for i in (1,2):
        a,bb=snaps[i-1][0],snaps[i][0]
        print(f"prompt {i+1} changed rooms:",{k:(a.get(k),bb.get(k)) for k in set(a)|set(bb) if a.get(k)!=bb.get(k)})
    # svg vs model agreement (scale 50, origin transform checked via widths/heights)
    for k,(x,y,w,d) in snaps[-1][0].items():
        sr=snaps[-1][1][k]; assert sr and abs(sr[2]/50-w)<1e-6 and abs(sr[3]/50-d)<1e-6,(k,sr,(w,d))
    print("SVG sizes == model sizes for all rooms: OK")
    # aspect ratio of rendered svg
    print("svg box:",pg.evaluate("(()=>{const s=document.querySelector('[id=rooms]').ownerSVGElement;const r=s.getBoundingClientRect();return [r.width,r.height,s.getAttribute('viewBox'),s.getAttribute('preserveAspectRatio')]})()"))
    # reload keeps project
    pg.reload(); pg.wait_for_timeout(2500); pg.screenshot(path=f"{OUT}/4_after_reload.png")
    print("after reload same id:",pg.evaluate("localStorage.getItem('gotec.project_id')")==pid, "svg present:",pg.locator("svg").count()>0)
    print("console errors:",errs[:5])
    b.close()
