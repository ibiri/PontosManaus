import streamlit as st
import pandas as pd
import simplekml
from io import BytesIO
import zipfile

# === CONFIG ===
st.set_page_config(page_title="Sorteio de Setores - Manaus", layout="centered")

# === TÍTULO ===
st.title("🎯 Sorteio de Setores Censitários - Manaus")

# === ENTRADAS ===
total_pontos = st.number_input("🔢 Total de pontos a sortear", min_value=1, max_value=500, value=50)
num_days = st.number_input("📅 Número de dias (arquivos KMZ)", min_value=1, max_value=100, value=34)

# === BOTÃO ===
if st.button("🚀 Gerar arquivos KMZ"):
    with st.spinner("Processando..."):

        # === URL do Google Sheets convertido para CSV
        url = "https://docs.google.com/spreadsheets/d/12St0kWrOAVs2k8ILIXZC-kchqIL6KrUuQpHXEutpnCY/export?format=csv"

        # === Leitura do CSV diretamente do Google Sheets
        df = pd.read_csv(url, delimiter=';')

        # === Mapeamento dos bairros para zonas
        bairro_zona_mapping = {
            'Adrianopólis': 'Centro-Sul', 'Águas Claras': 'Norte', 'Aleixo': 'Centro-Sul', 'Alvorada': 'Centro-Oeste',
            'Amazonino Mendes': 'Norte', 'Armando Mendes': 'Leste', 'Da paz': 'Centro-Oeste', 'União': 'Centro-Sul',
            'Betania': 'Sul', 'Cachoeirinha': 'Sul', 'Campos Sales': 'Oeste', 'Centro': 'Sul', 'Chapada': 'Centro-Sul',
            'Cidade de Deus': 'Norte', 'Cidade Nova': 'Norte', 'Colonia Antonio Aleixo': 'Leste', 'Colonia Oliveira Machado': 'Sul',
            'Colonia Santo Antonio': 'Norte', 'Colonia Terra Nova': 'Norte', 'Compensa': 'Oeste', 'Coroado': 'Leste',
            'Crespo': 'Sul', 'Dom Pedro': 'Centro-Oeste','Educandos': 'Sul', 'Flores': 'Centro-Sul', 'Gilberto Mestrinho': 'Leste', 'Gloria': 'Oeste', 'Grande Vitoria': 'Leste',
            'Japiim': 'Sul', 'Jardim Maua': 'Leste', 'Jorge Teixeira': 'Leste', 'Lago Azul': 'Norte', 'Lirio do Vale': 'Oeste',
            'Mauazinho': 'Leste', 'Monte das Oliveiras': 'Norte', 'Morro da Liberdade': 'Sul', 'Mutirão': 'Norte',
            'Nossa Senhora Aparecida': 'Sul', 'Nossa Senhora das Graças': 'Centro-Sul', 'Nossa Senhora de Fátima': 'Sul',
            'Nova Cidade': 'Norte', 'Nova Esperanca': 'Oeste', 'Novo Aleixo': 'Norte', 'Novo Israel': 'Norte',
            'Parque 10 de novembro': 'Centro-Sul', 'Parque das Nações': 'Leste', 'Petropolis': 'Sul', 'Planalto': 'Centro-Oeste',
            'Ponta Negra': 'Oeste', 'Praça 14': 'Sul', 'Presidente Vargas': 'Sul', 'Raiz': 'Sul', 'Redenção': 'Centro-Oeste',
            'Santa Etelvina': 'Norte', 'Santa Luzia': 'Sul', 'Santo Agostinho': 'Oeste', 'Santo Antonio': 'Oeste', 'Sao Francisco': 'Sul',
            'São Geraldo': 'Centro-Sul', 'Sao Jorge': 'Oeste', 'São José': 'Leste', 'São Lazaro': 'Sul', 'São Raimundo': 'Oeste',
            'Tancredo Neves': 'Leste', 'Taruma': 'Oeste', 'Taruma Açu': 'Oeste', 'Vila da Prata': 'Oeste', 'Zumbi': 'Leste'
        }

        df['ZONA'] = df['DSC_LOCALIDADE'].map(bairro_zona_mapping)
        setores_por_zona = df['CD_SETOR'].groupby(df['ZONA']).nunique()
        proporcoes = (setores_por_zona / 2992) * total_pontos
        proporcoes = proporcoes.round().astype(int)

        # Ajustar para garantir total exato de pontos
        while proporcoes.sum() != total_pontos:
            diff = total_pontos - proporcoes.sum()
            proporcoes.iloc[0] += diff

        # === Gerar arquivos KMZ e zipar em memória
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for day in range(1, num_days + 1):
                sampled_df = pd.DataFrame()
                for zona, n_pontos in proporcoes.items():
                    df_zona = df[df['ZONA'] == zona]
                    sampled_df_zona = df_zona.sample(n=n_pontos, random_state=day)
                    sampled_df = pd.concat([sampled_df, sampled_df_zona])

                sampled_df = sampled_df[['DSC_LOCALIDADE', 'CD_SETOR', 'ZONA', 'LATITUDE', 'LONGITUDE']]
                kml = simplekml.Kml()

                for _, row in sampled_df.iterrows():
                    desc = f"Bairro: {row['DSC_LOCALIDADE']}\nZona: {row['ZONA']}"
                    kml.newpoint(name=row['CD_SETOR'], description=desc, coords=[(row['LONGITUDE'], row['LATITUDE'])])

                kmz_buffer = BytesIO()
                kml.savekmz(kmz_buffer)
                kmz_buffer.seek(0)
                zip_file.writestr(f"sampled_data_day_{day}.kmz", kmz_buffer.read())

        zip_buffer.seek(0)
        st.success("✅ Arquivos KMZ gerados com sucesso!")

        st.download_button(
            label="📥 Baixar todos os arquivos (ZIP)",
            data=zip_buffer,
            file_name="KMZ_Sorteio_Manaus.zip",
            mime="application/zip"
        )

