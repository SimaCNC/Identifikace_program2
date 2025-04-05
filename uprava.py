import os
import pandas as pd

slozka = r"D:\Škola\8.Semestr\Identifikace_a_simulace\program2\SIM0370" #zde je potreba zadat adresa s daty s pripoonou .txt
nova_slozka = os.path.join(slozka, "upravene_data")

if not os.path.exists(nova_slozka):
    os.makedirs(nova_slozka)

for soubor in os.listdir(slozka):
    if soubor.endswith(".txt"):
        cesta_souboru = os.path.join(slozka, soubor)
        
        #otevreni souboru:
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

            novy_soubor = os.path.splitext(soubor)[0] + ".xlsx"
            cesta_novy_soubor = os.path.join(nova_slozka, novy_soubor)
            df.to_excel(cesta_novy_soubor, index=False)
            print(f"soubor {soubor} byl uspesne vytvoren")
        else:
            print(f"V souboru {soubor} nebyl nalezen prvni radek casu 0.00(0)")
print("hotovsono")
        

        