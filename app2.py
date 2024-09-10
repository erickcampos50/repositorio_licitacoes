import streamlit as st
import pandas as pd
import numpy as np
import time

@st.cache_data
def find_best_combination_random(df, target, margin=0.1, max_combination_size=20, max_time_per_iteration=10, unique_identification=True):
    """
    Encontra a melhor combinação de linhas de um DataFrame que se aproximam do valor objetivo médio especificado,
    dentro de uma margem de erro definida.

    Args:
        df (pd.DataFrame): O DataFrame contendo os dados.
        target (float): O valor objetivo médio.
        margin (float): A margem de erro permitida (default: 0.1).
        max_combination_size (int): O tamanho máximo da combinação (default: 20).
        max_time_per_iteration (int): O tempo máximo de execução por iteração em segundos (default: 10).
        unique_identification (bool): Se True, garante que os valores no campo "Identificação da Compra" sejam únicos (default: True).

    Returns:
        pd.DataFrame: A melhor combinação encontrada, ou None se nenhuma combinação for encontrada.
    """
    start_time = time.time()

    # Calcula a margem de erro
    lower_bound = target * (1 - margin)
    upper_bound = target * (1 + margin)
    
    # Limite individual de seleção
    individual_lower_bound = target * 0.7
    individual_upper_bound = target * 1.3

    # Embaralha o DataFrame para garantir combinações aleatórias
    df = df.sample(frac=1).reset_index(drop=True)
    
    # Filtra os valores que estão dentro do limite individual
    filtered_df = df[(df['Valor Unitário'] >= individual_lower_bound) & (df['Valor Unitário'] <= individual_upper_bound)]

    best_combination = None
    best_combination_size = 0

    # Itera por um número limitado de tentativas aleatórias até o tempo máximo de execução
    iterations = 0
    while time.time() - start_time < max_time_per_iteration:
        sample_df = filtered_df.sample(n=min(len(filtered_df), max_combination_size))
        
        # Remove duplicatas na "Identificação da Compra" se unique_identification for True
        if unique_identification:
            sample_df = sample_df.drop_duplicates(subset=['Identificação da Compra'])
        
        # Calcula a média dos valores unitários da combinação
        combo_mean = sample_df['Valor Unitário'].mean()
        iterations += 1
        print(f"Iteração {iterations}: média da combinação = {combo_mean}")
        
        # Verifica se a combinação atual é a melhor encontrada até agora
        if lower_bound <= combo_mean <= upper_bound:
            if best_combination is None or len(sample_df) > best_combination_size:
                best_combination = sample_df
                best_combination_size = len(sample_df)
                print(f"Nova melhor combinação encontrada com {best_combination_size} elementos.")

    return best_combination

def save_dataframe_to_csv(df, filename):
    df.to_csv(filename, index=False, sep=';')

st.title("Combinações Ótimas de Valores")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    # Leitura do arquivo CSV com separador ";"
    df = pd.read_csv(uploaded_file, sep=';')

    # Substitui a vírgula pelo ponto nos valores da coluna 'Valor Unitário' e converte para float
    df['Valor Unitário'] = df['Valor Unitário'].str.replace(',', '.').astype(float)

    st.write("Dados carregados:")
    st.write(df)

    # Parâmetros de entrada
    target_values = st.text_input("Digite os valores objetivos separados por vírgula (por exemplo, 200,300,450,500,650)", "200,300,450,500,650")
    target_values = [float(value.strip()) for value in target_values.split(",")]

    margin = st.slider("Margem de erro (%)", min_value=1, max_value=50, value=10) / 100
    max_combination_size = st.slider("Tamanho máximo da combinação", min_value=1, max_value=100, value=20)
    max_time_per_iteration = st.slider("Tempo máximo de execução por iteração (segundos)", min_value=1, max_value=120, value=10)
    unique_identification = st.checkbox("Somente valores únicos no campo 'Identificação da Compra'", value=True)

    # Processa cada valor objetivo
    results = {}
    file_paths = []
    for target_value in target_values:
        st.write(f"Processando valor objetivo: {target_value}")
        best_combination = find_best_combination_random(df, target_value, margin, max_combination_size, max_time_per_iteration, unique_identification)
        if best_combination is not None:
            file_name = f'best_combination_{target_value}.csv'
            save_dataframe_to_csv(best_combination, file_name)
            file_paths.append(file_name)
            results[target_value] = best_combination
            st.write(f"Combinação encontrada para {target_value}:")
            st.write(best_combination)
        else:
            st.write(f"Nenhuma combinação encontrada para {target_value} dentro da margem especificada.")
            results[target_value] = None

    # Exibe os resultados
    st.write("Resultados das Combinações:")
    for target_value, result in results.items():
        if result is not None:
            st.write(f"Valor objetivo {target_value}:")
            st.write(result)
            st.download_button(
                label=f"Baixar combinação para {target_value}",
                data=result.to_csv(index=False, sep=';'),
                file_name=f'best_combination_{target_value}.csv',
                mime='text/csv'
            )
