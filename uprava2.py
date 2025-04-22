"""
Tento program vznikl pro upravu dat do predmetu IaSS
datum 22.4.2025

Jak se program spousti: 
staci mit nainstalovane prislusne potrebne knihovny a moduly vit importy nize,
pote staci tento skript vlozit do slozky se zmerenymi daty (soubory vygenerovane RC2000)
a nasledne skript spustit, vytvori se slozka s nazvem "upravene_data" a zde jsou vsechny 
potrebne informace prevedene do .xlsx souboru a take jsou extrahovane hodnoty do prislusnych
souboru, ktere jsou pote potrebne pro analyzu a identifikaci systemu pomoci frekvencni identifikace
"""

import os
import re 
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

#STARE HLEDANI POSUNUTI - NENI INTERPOLOVANO
def najit_posunuti(signal, cas):
    """
    fazovy posun pocitam jako trojclenku: 
    2pi = T (=1/f)                                      
    fi = Tx 
    ,,.. kde Tx je posunuty cas kanalu B
    v mem pripade hledam cas kde je prvni hodnota <= 0
    prislusny cas pak odpovida fazovemu posunu
    """
    for t,y in zip(cas, signal):
        if y >= 0:
            return t
    return None

#INTERPOLACE MEZI 2 BODY
#typova anotace pro df, ze je to objekt z knihovny pd
def najit_posunuti_interpolovane(df: pd.DataFrame):
    for i in range(1, len(df)):
        y1 = df['CH B (V)'].iloc[i-1]
        y2 = df['CH B (V)'].iloc[i]
        if y1 < 0 <= y2:
            t1 = df['Cas (s)'].iloc[i-1]
            t2 = df['Cas (s)'].iloc[i]
            if y1 == 0:
                return t1
            else:
                t0 = t1 - y1 * (t2 - t1) / (y2 - y1)
                return t0
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

posun_old = 0

#GENEROVANI SOUBORU
for soubor, frekvence in seznam_souboru:
    cesta_souboru = os.path.join(slozka, soubor)
    with open(cesta_souboru, "r", encoding="utf-8") as f:
        radky = f.readlines()

    hlavicka = radky[15].lower()
    casova_zakladna = "ms" in hlavicka

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
        if casova_zakladna:
            df["Cas (s)"] *= 0.001 #prepocitano na milisekundy cas
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

        
        #vypocet posunuti
        t_B = najit_posunuti_interpolovane(df.iloc[:n])
        print(t_B)

        if t_B is not None:
            fazovy_posun_rad = -2 * pi * frekvence * t_B
            fazovy_posun_stupne = np.degrees(fazovy_posun_rad) #degrees pro interval -180 az +180°
        else:
            fazovy_posun_stupne = np.nan

        if posun_old < fazovy_posun_stupne:
            fazovy_posun_stupne = posun_old - 1 
        
        posun_old = fazovy_posun_stupne

        if fazovy_posun_stupne <= -180 or (t_B is None):
            fazovy_posun_stupne = -180

        #Nutno doupravit odkdy se fazovy posun ma rovnat 180/-180, dle vystupu z  print(fazovy_posun_stupne)
        if fazovy_posun_stupne == 0:
            fazovy_posun_stupne = -180
        print(fazovy_posun_stupne)

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