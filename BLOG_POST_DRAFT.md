# Building a Linux Driver for Thrustmaster Ferrari GT Experience: Part 1

## The Challenge
We started with a Thrustmaster Ferrari GT Experience steering wheel, a classic piece of hardware designed primarily for PC (Windows) and PS3. Our goal? Make it work seamlessly on a Raspberry Pi running Raspberry Pi OS. 

Linux support for these older or less common wheels can be hit or miss. While some Thrustmaster wheels have kernel drivers, the GT Experience often falls back to a basic HID joystick mode, which might miss out on features like Rumble Force or proper calibration.

## Step 1: Gathering Intelligence
Every good engineering project starts with documentation. We've gathered:
- The PC Manual
- The PS3 Manual
- The Windows Unified Drivers (2018.FFD.2)

These will be our primary sources for understanding how the device communicates. The Windows driver, while not directly runnable on Linux, contains valuable information that we might be able to extract or reverse-engineer.

## Step 2: První kontakt
Po zapojení volantu do Raspberry Pi jsme zjistili následující:
- **Identifikátory**: Vendor ID `044f`, Product ID `b655`.
- **Název**: Thrustmaster FGT Rumble 3-in-1.
- **Detekce**: Linux jej vidí jako standardní Gamepad přes ovladač `hid-generic`.

Z analýzy schopností (capabilities) vyplývá, že zařízení nabízí:
- Osu `ABS_X` (pravděpodobně volant).
- Osy `ABS_Y` a `ABS_RZ` (pravděpodobně pedály).
- Směrový kříž (D-Pad) přes `ABS_HAT0X` a `ABS_HAT0Y`.
- 13 tlačítek.

Nyní nás čeká ověření, jak tyto osy reagují v praxi. Jsou pedály na samostatných osách, nebo sdílejí jednu (kombinované pedály)? To zjistíme v dalším kroku.

> [!WARNING]
> Během testování jsme narazili na hlášení o podpětí (Undervoltage) v systému. To může způsobovat odpojování USB zařízení, takže budeme muset být opatrní na stabilitu zdroje napájení.

## Proč nestačí jen zapojit a hrát? (The "Why")
Mohlo by se zdát, že když Linux volant „vidí“, máme vyhráno. Ale praxe ukázala tři záludnosti:
1. **Pedál jako vypínač**: Kvůli inverzní logice (255=klid) byste v mnoha hrách stáli na plynu hned po startu, aniž byste se dotkli pedálu.
2. **Auto, co nejede naplno**: Protože plyn se zastaví na hodnotě 76 a brzda na 20, systém by bez kalibrace nikdy neaktivoval 100% stisk. Auto by jelo jako s polovičním plynem.
3. **Mrtvé zóny**: Surová data jsou „zubatá“. Náš driver je vyhlazuje a normalizuje na standardní rozsah 0-1024, kterému rozumí každý simulátor.

### Osy (EV_ABS)
- **Volant (ABS_X)**: Rozsah 0 (vlevo) až 255 (vpravo). Střed je na 128.
- **Plyn/Brzda (ABS_Y)**: Rozsah cca 76 až 255. Pozor, v klidu je hodnota 255!
- **Druhý pedál (ABS_RZ)**: Rozsah cca 17 až 255. Opět v klidu 255.
- **Směrový kříž (HAT0X/Y)**: Standardní hodnoty -1, 0, 1.

### Tlačítka (EV_KEY)
Zachytili jsme všech 13 tlačítek (kódy 304 až 316). To odpovídá bohaté výbavě tohoto modelu.

## Step 4: Virtuální ovladač – Finální vítězství
Vytvořili jsme `fgt_remapper.py`, který běží v uživatelském prostoru a provádí v reálném čase:
- **Normalizaci volantu**: Původních 0–255 mapuje na přesných 0–1024.
- **Opravu pedálů**: Odpovídá na inverzní logiku (255 = nic, 76/20 = plný plyn/brzda) a převádí ji na standardní 0–100 % (v našem případě 0–1024).
- **Emulaci standardního Gamepadu**: Pro systém se tváří jako standardní herní zařízení, kterému rozumí každá moderní hra.

- **Exkluzivní přístup (Grab)**: Ovladač si fyzické zařízení „přivlastní“, takže systém (a hlavně prohlížeč u GeForce Now) nevidí dva různé vstupy, což by způsobovalo chaos v ovládání.
- **Automatizace skrze Systemd**: Ovladač běží jako služba na pozadí, která se sama aktivuje při startu nebo připojení zařízení.

## Závěr
Z obyčejného „kusu plastu“, který na Linuxu zlobil s pedály a měl divné rozsahy, jsme udělali plnohodnotný herní ovladač. Raspberry Pi teď slouží jako mozek, který opravuje nedokonalosti starého hardwaru.

Tato výzva nám ukázala, že i bez oficiálních ovladačů od výrobce si komunita (a šikovná AI) dokáže poradit. Tak co, uvidíme se na startu?

---
*Projekt vyvinut ve spolupráci s Antigravity (Advanced Agentic Coding team @ Google DeepMind).*
