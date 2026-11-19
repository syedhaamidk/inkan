import app
c = app.app.test_client()
def test_flow():
    ca = c.post("/api/ca", json={"name": "T"}).get_json()
    leaf = c.post("/api/issue", json={"ca_cert": ca["cert"], "ca_key": ca["key"], "hostname": "a.example.com"}).get_json()
    ok = c.post("/api/verify", json={"cert": leaf["cert"], "ca_cert": ca["cert"], "hostname": "a.example.com"}).get_json()
    assert ok["valid"]
    assert not c.post("/api/verify", json={"cert": leaf["cert"], "ca_cert": ca["cert"], "hostname": "b.example.com"}).get_json()["valid"]
    other = c.post("/api/ca", json={}).get_json()
    assert not c.post("/api/verify", json={"cert": leaf["cert"], "ca_cert": other["cert"], "hostname": "a.example.com"}).get_json()["valid"]
    exp = c.post("/api/issue", json={"ca_cert": ca["cert"], "ca_key": ca["key"], "hostname": "a.example.com", "expired": True}).get_json()
    assert not c.post("/api/verify", json={"cert": exp["cert"], "ca_cert": ca["cert"], "hostname": "a.example.com"}).get_json()["valid"]
def test_bad_input():
    assert c.post("/api/issue", json={"hostname": "bad host!"}).status_code == 400
    assert c.post("/api/inspect", json={"cert": "nope"}).status_code == 400
def test_lab_and_static():
    assert all(r["ok"] for r in c.post("/api/lab").get_json()["results"])
    assert c.get("/").status_code == 200 and c.get("/healthz").status_code == 200
