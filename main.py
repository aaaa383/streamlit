import streamlit as st
import pandas as pd


# 各炉の容量
furnace_dict = {
    "ST01": 22000,
    "ST02": 22000,
    "ST03": 22000,
    "ST04": 22000,
    "ST05": 22000,
    "ST06": 8800
    }


# 貪欲法を解く
def solve_greedy(data, heat_list, capacity):
    
  total_dict = {}
  parts_dict = {}

  for heat in heat_list:
    # ヒートNO毎に重い順で詰め込んでいく
    data_ = data[data['ヒートNO'] == heat]
    data_sort = data_.sort_values(by="重量" ,ascending=False)

    total_size = 0
    parts_list = []

    for low in data_sort.iterrows():
      if low[1]['重量'] + total_size <= capacity:
        total_size += low[1]['重量']
        parts_list.append(low[1]['品番'])
      
      # データの集計
      total_dict[heat] = total_size
      parts_dict[heat] = parts_list
  
  # 一番詰められた組み合わせの算出とその場合の結果の格納
  optimal_solution = max(total_dict.items(), key=lambda x: x[1])
  solution_parts_list = parts_dict[optimal_solution[0]]

  data['探索解'] = data['品番'].isin(solution_parts_list) * 1

  return optimal_solution, data


# タイトルを表示
st.title('数理最適化サンプルツール')

st.sidebar.markdown("### 1. データの読み込み")
uploaded_file = st.sidebar.file_uploader("CSVファイルをドラッグ&ドロップ、またはブラウザから選択してください", type='csv', key='train')
if uploaded_file is not None:

    #データの読込み
    df = pd.read_csv(uploaded_file, encoding='shift-jis')

     #データの表示
    st.sidebar.markdown("### 2. データの情報の表示")
    if st.sidebar.checkbox('データの中身を表示しますか？'):
        st.markdown("### 1. アップロードされたデータを確認します")
        st.dataframe(df)

        furnace = st.selectbox(label="炉を選んでください",
             options=furnace_dict.keys())

        # 使う炉のキャパシティ
        capacity = furnace_dict[furnace]

    # チェック時に上で求めた条件で数理最適化を解く
    st.sidebar.markdown("### 3. 数理最適化の求解")
    if st.sidebar.checkbox('最適化を行いますか？'):
        st.markdown("### 2. 数理最適化の結果を表示")
        
        heat_list = df['ヒートNO'].unique().tolist()
        optimal_solution, data = solve_greedy(df, heat_list, capacity)

        # 結果の表示
        result = pd.DataFrame([optimal_solution], columns=['ヒートNO', '計画重量'])
        st.dataframe(result)
        
        st.dataframe(data)
    
    st.sidebar.markdown("### 3. csvダウンロード")
    if st.sidebar.checkbox('csvダウンロード画面を表示しますか？'):
        st.markdown("### 3. 結果のダウンロード")

        st.download_button(
            label='ダウンロードボタン',
            data=data.to_csv(index=None).encode('utf-8'),
            file_name='result.csv'
        )

        