import streamlit as st
import numpy as np
import pandas as pd
import datetime


# 各炉の容量
furnace_dict = {
    "ST01": 22000,
    "ST02": 22000,
    "ST03": 22000,
    "ST04": 22000,
    "ST05": 22000,
    "ST06": 8800
    }


# 制約条件(品番によっては使えない炉が存在する)
ST06_NG = ['NDA06981' ,'294157-0143'] # ST06に入れてはいけない
ST06_ONLY = ['HDA07464','TYA05090']   # ST06でのみ処理可能

# 制約条件(デンソー主流品リストに含まれるパーツは優先的に作る)
DENSO_list = [
  'NDA07024',
  'NDA06292',
  'NDA06279',
  'NDA06302',
  'NDA07005',
  'NDA06287',
  'NDA07020',
  'NDA06999',
  'NDA07001',
  'NDA07011',
  'NDA07010',
  'NDA07012',
  'NDA07013',
  'NDA06868'
]

# 部品マスターデータ
mastor = pd.read_csv('parts_matstor.csv', encoding="cp932", index_col=None)

# 営業日の計算
def business_days(start, end):
    mask = pd.notnull(start) & pd.notnull(end)
    start = start.values.astype('datetime64[D]')[mask]
    end = end.values.astype('datetime64[D]')[mask]
    result = np.empty(len(mask), dtype=float)
    result[mask] = np.busday_count(start, end)
    result[~mask] = np.nan
    return result


def solve_greedy(data, heat_list, furnace_name):
    
  total_dict = {}
  priority_dict = {}
  parts_dict = {}

  # masterデータとマージ
  mastor = pd.read_csv('parts_matstor.csv', encoding="cp932", index_col=None)
  data = pd.merge(data, mastor, on='品番')
  data['today'] = datetime.date.today()

  # 営業日を考慮した締め切りまでの計算
  data['date_diff'] = business_days(data['today'], data['客先（出荷）納期'])

  # 納期直前のデータを抽出
  deadline = data[data['現在日時と精線引抜納期差異']==0].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])

  # 熱処理２回目で優先度高いものを投入
  heat_2 = data[(data['熱処理回数'] == 2) & (data['状態'] == "荒引")].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])

  for heat in heat_list:
    # ヒートNO毎に重い順で詰め込んでいく
    data_ = data[data['ヒート'] == heat]
    data_sort = data_.sort_values(by=["優先ランク②","重量"] , ascending=[True,False])

    total_size = 0
    total_priority = 0
    parts_list = []
    
    if furnace_name in ['ST01', 'ST02', 'ST03', 'ST04', 'ST05']:
      
      # 納期直前のデータは予め投入しておく
      if len(deadline) > 0:
        deadline_heat_list = deadline['ヒート'].unique().tolist()
        for dead_heat in deadline_heat_list:
          data_heat = data[data['ヒート'] == dead_heat].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])
          for deadline_data in data_heat.iterrows():
            if deadline_data[1]['重量'] + total_size <= 22000:
              total_size += deadline_data[1]['重量']
              total_priority += deadline_data[1]['優先ランク②']
              parts_list.append(deadline_data[1]['品番'])
        
      # 熱処理2回目のデータは予め投入しておく
      elif len(heat_2) > 0:
        heat_2_list = heat_2['ヒート'].unique().tolist()
        for heat_2_ in heat_2_list:
          data_heat_2 = data[data['ヒート'] == heat_2_].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])
          for heat_data in data_heat_2.iterrows():
            if heat_data[1]['重量'] + total_size <= 22000:
              total_size += heat_data[1]['重量']
              total_priority += heat_data[1]['優先ランク②']
              parts_list.append(heat_data[1]['品番'])

      else:
        for low in data_sort.iterrows():
          if low[1]['品番'] in ST06_ONLY or (low[1]['date_diff'] >= 5 and low[1]['品番'] not in DENSO_list):
            continue
      
          # 容量以下になるように備品を詰め込む
          if low[1]['重量'] + total_size <= 22000:
            total_size += low[1]['重量']
            total_priority += low[1]['優先ランク②']
            parts_list.append(low[1]['品番'])
      
      # 重量が20000以下なら計画しない
      if total_size < 20000:
        continue

      # データの集計
      total_dict[heat] = total_size
      priority_dict[heat] = total_priority
      parts_dict[heat] = parts_list
  
    else:
          
      # 納期直前のデータは予め投入しておく
      if len(deadline) > 0:
        deadline_heat_list = deadline['ヒート'].unique().tolist()
        for dead_heat in deadline_heat_list:
          data_heat = data[data['ヒート'] == dead_heat].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])
          for deadline_data in data_heat.iterrows():
            if deadline_data[1]['重量'] + total_size <= 8800:
              total_size += deadline_data[1]['重量']
              total_priority += deadline_data[1]['優先ランク②']
              parts_list.append(deadline_data[1]['品番'])
      
      # 熱処理2回目のデータは予め投入しておく
      elif len(heat_2) > 0:
        heat_2_list = heat_2['ヒート'].unique().tolist()
        for heat_2_ in heat_2_list:
          data_heat_2 = data[data['ヒート'] == heat_2_].sort_values(by=["優先ランク②","重量"] , ascending=[True,False])
          for heat_data in data_heat_2.iterrows():
            if heat_data[1]['重量'] + total_size <= 8800:
              total_size += heat_data[1]['重量']
              total_priority += heat_data[1]['優先ランク②']
              parts_list.append(heat_data[1]['品番'])
      
      else:
        for low in data_sort.iterrows():
          if low[1]['品番'] in ST06_NG or (low[1]['date_diff'] >= 5 and low[1]['品番'] not in DENSO_list):
            continue
            
          if low[1]['重量'] + total_size <= 8800:
            total_size += low[1]['重量']
            total_priority += low[1]['優先ランク②']
            parts_list.append(low[1]['品番'])

      # 重量が8000以下なら計画しない
      if total_size < 8000:
        continue

      # データの集計
      total_dict[heat] = total_size
      priority_dict[heat] = total_priority
      parts_dict[heat] = parts_list


  # 一番詰められた組み合わせの算出とその場合の結果の格納
  # optimal_solution = max(total_dict.items(), key=lambda x: x[1])

  # 一番優先度の合計が少ない組み合わせの算出とその場合の結果の格納
  optimal_solution = min(priority_dict.items(), key=lambda x: x[1])
  solution_parts_list = parts_dict[optimal_solution[0]]

  weight_df = pd.DataFrame(
    data={
        '選択した炉': furnace_name, 
        '重量': [total_dict[optimal_solution[0]]]}
        )

  data['計画有無'] = data['品番'].isin(solution_parts_list) * 1

  return weight_df, data

# タイトルを表示
st.title('数理最適化サンプルツール')

st.sidebar.markdown("### 1. データの読み込み")
name = st.sidebar.text_input('EXCELシート名を入力してください')
uploaded_file = st.sidebar.file_uploader("EXCELファイルをドラッグ&ドロップ、またはブラウザから選択してください", key='train')
if uploaded_file is not None:

  #データの読込み
  df = pd.read_excel(
    uploaded_file
    ,engine='openpyxl'
    ,sheet_name=name
    ,skiprows=[0,1,3]
    ,usecols='A:Y'
  )

  #データの表示
  st.sidebar.markdown("### 2. データの情報の表示")
  if st.sidebar.checkbox('データの中身を表示しますか？'):
    st.markdown("### 1. アップロードされたデータを確認します")
    st.dataframe(df)

    furnace = st.selectbox(label="炉を選んでください",
      options=furnace_dict.keys())

  # チェック時に上で求めた条件で数理最適化を解く
  st.sidebar.markdown("### 3. 数理最適化の求解")
  if st.sidebar.checkbox('最適化を行いますか？'):
    st.markdown("### 2. 計画されたヒートNO")
        
    heat_list = df['ヒート'].unique().tolist()
    weight_df, data = solve_greedy(df, heat_list, furnace)

    # 無駄な列の削除
    data = data.drop(['today','date_diff'],axis=1)
    
    # 表示する用のdataframeにデータを絞り込む
    display_data = data[["客先（出荷）納期", "優先ランク②", "品番", "重量", "ヒート", "状態", "本日入荷・荒引き日", "計画有無"]]

    # 結果の表示
    st.dataframe(weight_df)
    st.dataframe(display_data)

    st.sidebar.markdown("### 3. csvダウンロード")
    if st.sidebar.checkbox('csvダウンロード画面を表示しますか？'):
      st.markdown("### 3. 結果のダウンロード")

      st.download_button(
        label='ダウンロードボタン',
        data=data.to_csv(index=None).encode('cp932'),
        file_name='result.csv'
      )
