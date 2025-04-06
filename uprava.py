import os
import re #regular expression
import pandas as pd
from math import pi
from scipy.signal import correlate
import numpy as np



def extrahuj_frekvenci(nazev):
    """
    extrahuje frekvenci z nazvu jako float
    napriklad 'F43_6A5.txt' znamena frekvence 43,6 a amplituda 5
    """
    shoda = re.match(r"F(\d+)_?(\d)A", os.path.splitext(nazev)[0])
    if shoda:
        cela = shoda.group(1)
        desetina = shoda.group(2)
        frekvence = float(f"{cela}.{desetina}")
        return frekvence
    return None

#vytvoreni slozky
slozka = os.getcwd() #zde je python skript primo ve slozce
nova_slozka = os.path.join(slozka, "upravene_data")
if not os.path.exists(nova_slozka):
    os.makedirs(nova_slozka)

#ziskani a serazeni souboru
seznam_souboru = []
for soubor in os.listdir(slozka):
    if soubor.endswith(".txt"):
        frekvence_souboru = extrahuj_frekvenci(soubor)
        if frekvence_souboru is not None:
            seznam_souboru.append((soubor, frekvence_souboru))

#serazeni podle frekvence
seznam_souboru.sort(key=lambda x: x[1])

vysledky_frekvence = []
vysledky_omega = []
vysledky_amplituda_A = []
vysledky_amplituda_B = []
vysledky_amplituda = []
vysledky_tFi = []
vysledky_PhaseShiftStupne = []
vysledky_PhaseShiftRad = []

for soubor, frekvence in seznam_souboru:
    cesta_souboru = os.path.join(slozka, soubor)
    with open(cesta_souboru, "r", encoding="utf-8") as f:
        radky = f.readlines()

    x = -1
    for i, radek in enumerate(radky):
        if radek.strip() != "" and radek[0] == '0':
            x = i
            break

    if x != -1:
        nove_radky = radky[x:]
        data = [line.strip().split("\t") for line in nove_radky]
        df = pd.DataFrame(data, columns=["Cas (s)", "CH A (V)", "CH B (V)"])
        
        #prislusne data
        df["Cas (s)"] = pd.to_numeric(df["Cas (s)"], errors="coerce")
        df["CH A (V)"] = pd.to_numeric(df["CH A (V)"], errors="coerce")
        df["CH B (V)"] = pd.to_numeric(df["CH B (V)"], errors="coerce")

        cas = df['Cas (s)']
        ch_a = df['CH A (V)']
        ch_b = df['CH B (V)']

        #mene period
        n = 100
        ch_a_use = ch_a[:n]
        ch_b_use = ch_b[:n]

        #maximalni amplitudy
        amplituda_a = ch_a_use.abs().max()
        amplituda_b = ch_b_use.abs().max()

        #vysledky frekvence
        vysledky_frekvence.append(frekvence)

        #vysledky omega
        omega = frekvence * 2 * pi
        vysledky_omega.append(omega)

        #vysledky amplituda A,B
        vysledky_amplituda_A.append(amplituda_a)
        vysledky_amplituda_B.append(amplituda_b)

        #pomer amplitud
        amplitudy_pomer = amplituda_b / amplituda_a
        
        #pripsani do vysledku amplitudy
        vysledky_amplituda.append(amplitudy_pomer)

        
        #casova skala je pravidela 
        doba_vzorku = cas.iloc[1] - cas.iloc[0]
        frekvence_vzorkovani = 1/doba_vzorku

        #krizova korelace
        korelace = correlate(ch_a_use, ch_b_use, mode='full')

        zpozdeni = np.arange(-len(ch_a_use)+1, len(ch_a_use))

        max_index = np.argmax(korelace)

        posun_v_case = zpozdeni[max_index]

          
        casove_zpozdeni = posun_v_case * doba_vzorku

        perioda = 1 / frekvence  # frekvence je z názvu souboru
        fazovy_posun_stupne = (casove_zpozdeni / perioda) * 360
        fazovy_posun_stupne = ((fazovy_posun_stupne + 180) % 360) - 180
        vysledky_PhaseShiftStupne.append(fazovy_posun_stupne)
        

        
        

        novy_soubor = os.path.splitext(soubor)[0] + ".xlsx"
        cesta_novy_soubor = os.path.join(nova_slozka, novy_soubor)
        df.to_excel(cesta_novy_soubor, index=False)

        print(f"soubor {soubor} byl uspesne vytvoren")
    else:
        print(f"V souboru {soubor} nebyl nalezen prvni radek casu 0.00(0)")

#Celkove vysledky Data Frame:
df_vysledky = pd.DataFrame({
    "Frekvence (Hz)": vysledky_frekvence,
    "Omega (rad/s)": vysledky_omega,
    "U (CH A)": vysledky_amplituda_A,
    "Y (CH B)": vysledky_amplituda_B,
    "Amplitudy B/A (-)": vysledky_amplituda,
    "Posun (°)": vysledky_PhaseShiftStupne
})

omega_df = pd.DataFrame([vysledky_omega])
omega_soubor = os.path.join(nova_slozka, "2omega.xlsx")
omega_df.to_excel(omega_soubor, index=False, header=False)

amplitudy_df = pd.DataFrame([vysledky_amplituda])
amplitudy_soubor = os.path.join(nova_slozka, "1amplitudy.xlsx")
amplitudy_df.to_excel(amplitudy_soubor, index=False, header=False)

posun_df = pd.DataFrame([vysledky_PhaseShiftStupne])
posun_soubor = os.path.join(nova_slozka, "3posun.xlsx")
posun_df.to_excel(posun_soubor, index=False, header=False)


print("hotovsono")




        