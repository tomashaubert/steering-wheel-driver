# Oživení volantu Thrustmaster FGT: Technický pohled pod kapotu

**Autor:** Tomáš Haubert  
**Datum:** 4. ledna 2026

Jak donutit 15 let starý volant, aby fungoval s moderním Cloud Gamingem na Linuxu? To byla výzva, které jsem čelil s modelem **Thrustmaster Ferrari GT Experience (FGT) 3-in-1**.

Ačkoliv Linux zařízení „viděl“, pro hraní bylo nepoužitelné. Pedály byly invertované, rozsahy neúplné a co je nejdůležitější – moderní webové prohlížeče (Xbox Cloud Gaming, GeForce Now) si s ním nevěděly rady.

Zde je technický popis cesty k vytvoření uživatelského ovladače v Pythonu, který tyto problémy řeší.

## 1. Analýza hardwaru

Prvním krokem bylo pochopit, co hardware vlastně odesílá. Pomocí nástroje `evtest` a vlastního Python skriptu jsme zachytili surové HID reporty.

**ID zařízení:** `044f:b655`

### „Surová“ data
Okamžitě jsme narazili na tři problémy:

1.  **Inverzní logika:** Pedály v klidu odesílaly hodnotu `255` a při sešlápnutí klesaly k `0`. Většina her očekává `0` v klidu a `255` (nebo více) při stisku.
2.  **Mrtvé zóny a limity:**
    *   **Plyn:** Při plném sešlápnutí klesl jen na `76` (nikoliv na `0`).
    *   **Brzda:** Při plném sešlápnutí klesla jen na `20` (nikoliv na `0`).
    *   *Výsledek:* Ve hře byste nikdy nedosáhli 100 % plynu nebo brzdění.
3.  **Zvláštní mapování:**
    *   **Plyn** byl na kódu události `5` (často ABS_RZ).
    *   **Brzda** byla na kódu události `1` (často ABS_Y).

## 2. Řešení: Userspace Remapper

Místo psaní jaderného modulu (což je náročné na údržbu) jsem zvolil přístup v uživatelském prostoru (userspace) pomocí `python-evdev` a `uinput`. To nám umožňuje:
1.  **Přivlastnit si (Grab)** fyzické zařízení (skrýt ho před OS).
2.  **Číst** surové události.
3.  **Zpracovat/Pře mapovat** hodnoty.
4.  **Vložit** čisté události do virtuálního zařízení.

### Algoritmus

Implementovali jsme lineární mapovací funkci s ořezem (clamping) pro vyřešení podivných hardwarových rozsahů:

```python
def map_val(val, in_min, in_max, out_min, out_max):
    # Oříznutí vstupu na hardwarové limity
    true_min = min(in_min, in_max)
    true_max = max(in_min, in_max)
    val = max(min(val, true_max), true_min)
    
    # Normalizace pozice (0.0 - 1.0)
    norm = (val - in_min) / (in_max - in_min)
    
    # Škálování na výstup
    return int(out_min + norm * (out_max - out_min))
```

Tato jednoduchá funkce řeší jak inverzi (prohozením min/max), tak kalibraci rozsahu (použitím 76/20 jako limitů).

## 3. Průlom s „Xbox Mode“

Největší překážkou byl Cloud Gaming. Prohlížeče spoléhají na standardní **Gamepad API**. Staré volanty s protokolem DirectInput se na tento standard často nemapují správně.

Abychom to vyřešili, vytvořili jsme místo obecného joysticku virtuální **ovladač Xbox 360**.

*   **Volant (Osa 0)** -> Mapován na Levou páčku X (`ABS_X`)
*   **Plyn (Osa 5)** -> Mapován na Pravý Trigger (`ABS_RZ`)
*   **Brzda (Osa 1)** -> Mapována na Levý Trigger (`ABS_Z`)

To byla magická kulka. Jakmile jsme emulovali XInput zařízení, Xbox Cloud Gaming okamžitě rozpoznal ovladač a triggery poskytly přesné analogové ovládání plynu a brzdy.

## 4. Automatizace

Aby se jednalo o skutečný „driver“, musí být neviditelný. Použili jsme `systemd` pro automatické spuštění remapperu.

**Soubor služby (`fgt-remapper.service`):**
```ini
[Service]
ExecStart=/usr/bin/python3 /cesta/k/driveru.py --mode xbox
Restart=always
```

## Závěr

S přibližně 200 řádky Pythonu jsme proměnili potenciální elektroodpad v plně funkční ovladač pro cloudové hraní. Latence je zanedbatelná a zážitek je srovnatelný s moderním hardwarem.

Celý zdrojový kód a návod k instalaci najdete na mém GitHubu.