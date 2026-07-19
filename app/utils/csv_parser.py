import pandas as pd

def ler_csv_inter(path):
    df = pd.read_csv(path, sep=";", encoding="utf-8")
    registros=[]

    for _,row in df.iterrows():
        registros.append({
            "descricao":row["Descrição"],
            "valor":row["Valor"],
            "data":row["Data"]
        })

    return registros