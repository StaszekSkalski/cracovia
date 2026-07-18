import requests, csv, os, json
from collections import Counter
from datetime import datetime, timezone, timedelta

EVENT = 9643
BASE = "https://bilety.cracovia.pl"
POMIN = {"KANAPA KIBICA"}


def nowa_sesja():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": BASE,
        "Referer": f"{BASE}/Stadium?eventId={EVENT}",
    })
    s.get(f"{BASE}/Stadium?eventId={EVENT}")
    return s


def raport():
    s = nowa_sesja()

    def get(name):
        return s.post(f"{BASE}/Stadium/{name}", params={"eventId": EVENT}).json()

    names = {sec["id"]: sec["name"] for sec in get("GetWGLSectors")["sectors"]}
    total = Counter(seat["sectorId"] for seat in get("GetWGLSeats")["seats"])

    free = {}
    for sec in get("GetWGLSectorsInfo")["sectors"]:
        free[sec["id"]] = sum(pa["freeSeatsNo"] for pa in sec["freeSeatsByPriceArea"])

    czas = datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d %H:%M")
    sektory, suma_z, suma_w = [], 0, 0

    for sid in sorted(total, key=lambda i: str(names.get(i, ""))):
        nazwa = str(names.get(sid, sid))
        if nazwa in POMIN:
            continue
        w = total[sid]
        z = w - free.get(sid, 0)
        suma_z += z
        suma_w += w
        sektory.append({"nazwa": nazwa, "zajete": z, "wszystkie": w,
                        "procent": round(z / w * 100, 1)})

    return czas, suma_z, suma_w, sektory


def zapisz_csv(czas, zajete, wszystkie):
    nowy = not os.path.exists("historia.csv")
    with open("historia.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if nowy:
            w.writerow(["czas", "zajete", "wszystkie", "procent"])
        w.writerow([czas, zajete, wszystkie, round(zajete / wszystkie * 100, 2)])


if __name__ == "__main__":
    czas, z, w, sektory = raport()

    with open("dane.json", "w", encoding="utf-8") as f:
        json.dump({"czas": czas, "zajete": z, "wszystkie": w,
                   "procent": round(z / w * 100, 1), "sektory": sektory},
                  f, ensure_ascii=False, indent=2)

    zapisz_csv(czas, z, w)
    print(f"{czas}  {z}/{w} = {z/w:.1%}")
